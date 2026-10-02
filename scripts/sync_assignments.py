#!/usr/bin/env python3
"""
Sync pages marked `assignment: true` in their frontmatter to Spring assignments.

    python3 scripts/sync_assignments.py                  # dry run: review only
    PAGES_BOT_PASSWORD=... python3 scripts/sync_assignments.py   # production

Flow: find pages -> build an Assignment per page -> merge copies of the same page
-> send each to Spring, which creates or updates by contentUrl (no duplicate rows).
Bad frontmatter never stops the run; it becomes a warning and a default value.
"""
import argparse
import json
import math
import os
import re
import sys
import time
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from urllib.parse import quote

import requests
import yaml

# Defaults for missing or invalid frontmatter.
DEFAULT_POINTS = 1.0
DEFAULT_DESCRIPTION = ""
DEFAULT_DUE_DATE = None
DEFAULT_SUBMISSION_TYPE = None
DEFAULT_CREATOR_UIDS = ("toby",)  # system test user; trailing comma keeps it a tuple
DEFAULT_COURSE_CODES = ()

PAGE_EXTENSIONS = {".md", ".markdown", ".html", ".htm", ".ipynb"}
# Registered-project build outputs; their sources under _projects are scanned instead.
GENERATED_ROOTS = {("_notebooks", "projects"), ("_posts", "projects"), ("_sass", "projects")}
FRONTMATTER_RE = re.compile(r"^\ufeff?\s*---\s*\n(.*?)\n---\s*(?:\n|$)", re.S)
PAGE_SUFFIX_RE = re.compile(r"\.(md|markdown|html|htm|ipynb)$", re.I)


class AssignmentDataError(ValueError):
    """Frontmatter that cannot become an assignment."""


# ---------------------------------------------------------------- reporting

class SyncReport:
    """Counts outcomes; warnings are bad page data, errors are infrastructure failures."""

    def __init__(self):
        self.sent = 0
        self.skipped = 0
        self.errors = []

    def warn(self, message, path=None):
        location = f" file={path}" if path else ""
        print(f"::warning{location}::{message}", file=sys.stderr)

    def skip(self, message, path=None):
        self.skipped += 1
        self.warn(f"Skipped: {message}", path)

    def error(self, message):
        self.errors.append(message)
        print(f"::error::{message}", file=sys.stderr)

    def summary(self, total):
        return f"Done: {total} assignments, {self.sent} sent, {self.skipped} skipped, {len(self.errors)} errors."

    @property
    def exit_code(self):
        return 2 if self.errors else 0


# ---------------------------------------------------------------- reading pages

def find_pages(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in PAGE_EXTENSIONS:
            continue
        if path.relative_to(root).parts[:2] in GENERATED_ROOTS:
            continue
        yield path


def parse_frontmatter(text: str):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return None


def read_frontmatter(path: Path):
    """Return the page's frontmatter dict, or None if it has none or can't be read."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    if path.suffix.lower() != ".ipynb":
        data = parse_frontmatter(text)
        return data if isinstance(data, dict) else None

    try:
        cells = json.loads(text).get("cells", [])
    except (ValueError, AttributeError):
        return None
    for cell in cells:
        source = cell.get("source")
        if isinstance(source, list):
            # Notebook lines may lack trailing newlines; rejoin so YAML stays parseable.
            source = "\n".join(str(line).rstrip("\n") for line in source)
        if isinstance(source, str):
            data = parse_frontmatter(source)
            if data is not None:
                return data if isinstance(data, dict) else None
    return None


# ---------------------------------------------------------------- Jekyll URL rules
# contentUrl must equal Jekyll's `page.url` byte for byte: Spring dedups on it, and
# the browser posts `page.url` from _layouts/post.html.

def canonicalize_content_url(url):
    """Mirrors AssignmentContentUrls.canonicalize in Spring; keep the two in step."""
    if not isinstance(url, str):
        return None
    return re.sub(r"/{2,}", "/", url.strip()).strip("/") or None


def jekyll_categories(relative_path: str, fm: dict):
    """Only directories above `_posts` are categories; frontmatter overrides them."""
    declared = fm.get("categories")
    if declared is None:
        declared = fm.get("category")
    if isinstance(declared, str):
        categories = declared.replace(",", " ").split()
    elif isinstance(declared, list):
        categories = [str(c).strip() for c in declared if str(c).strip()]
    else:
        categories = [part for part in relative_path.partition("_posts/")[0].split("/") if part]
    return [quote(c.lower(), safe="") for c in categories]


def content_url_for(root: Path, path: Path, fm: dict):
    permalink = fm.get("permalink")
    if isinstance(permalink, str) and permalink.strip():
        return canonicalize_content_url(permalink)

    relative = path.relative_to(root).as_posix()
    if "_posts/" in relative:
        dated = re.match(r"^(\d{4})-(\d{2})-(\d{2})-(.+)$", PAGE_SUFFIX_RE.sub("", path.name))
        if dated:
            year, month, day, slug = dated.groups()
            parts = jekyll_categories(relative, fm) + [year, month, day, slug]
            return canonicalize_content_url("/".join(parts) + ".html")

    relative = re.sub(r"(^|/)index\.(md|markdown|html|htm)$", r"\1", relative, flags=re.I)
    return canonicalize_content_url(PAGE_SUFFIX_RE.sub(".html", relative))


# ---------------------------------------------------------------- the assignment

@dataclass(frozen=True)
class Assignment:
    path: Path
    content_url: str
    name: str
    description: str = DEFAULT_DESCRIPTION
    points: float = DEFAULT_POINTS
    due_date: str | None = DEFAULT_DUE_DATE
    submission_type: str | None = DEFAULT_SUBMISSION_TYPE
    # None means "not declared"; defaults are applied only after copies are merged.
    creator_uids: tuple | None = None
    course_codes: tuple | None = None

    @classmethod
    def from_frontmatter(cls, root: Path, path: Path, fm: dict, report: SyncReport):
        content_url = content_url_for(root, path, fm)
        if not content_url:
            raise AssignmentDataError("could not determine contentUrl")
        return cls(
            path=path,
            content_url=content_url,
            name=_text(fm.get("title") or fm.get("name"), "title", path, report) or path.stem,
            description=_text(fm.get("description"), "description", path, report) or DEFAULT_DESCRIPTION,
            points=_points(fm.get("points"), path, report),
            due_date=_text(fm.get("dueDate") or fm.get("due_date") or fm.get("due"), "dueDate", path, report)
            or DEFAULT_DUE_DATE,
            submission_type=_text(fm.get("assignment_submission_type"), "assignment_submission_type", path, report)
            or DEFAULT_SUBMISSION_TYPE,
            creator_uids=_creator_uids(fm, path, report),
            course_codes=_course_codes(fm, path, report),
        )

    SYNC_FIELDS = ("submission_type", "creator_uids", "course_codes")

    def merge(self, other: "Assignment") -> "Assignment":
        """Combine two copies of one page (e.g. a notebook and its converted post).

        Declared sync fields must agree; one copy may fill in what the other omits.
        The notebook is the editable source, so its display text wins.
        """
        preferred = other if other.path.suffix.lower() == ".ipynb" else self
        merged = {}
        for field in self.SYNC_FIELDS:
            mine, theirs = getattr(self, field), getattr(other, field)
            if mine is not None and theirs is not None and mine != theirs:
                raise AssignmentDataError(
                    f"conflicting {field} for '{self.content_url}' in {self.path} and {other.path}"
                )
            merged[field] = mine if mine is not None else theirs
        return replace(preferred, **merged)

    def with_defaults(self) -> "Assignment":
        return replace(
            self,
            creator_uids=self.creator_uids or DEFAULT_CREATOR_UIDS,
            course_codes=self.course_codes or DEFAULT_COURSE_CODES,
        )

    def to_payload(self) -> dict:
        # Form lists become repeated fields; empty lists and None are not sent at all.
        payload = {
            "name": self.name,
            "contentUrl": self.content_url,
            "description": self.description,
            "points": self.points,
            "creatorUids": list(self.creator_uids or ()),
            "courseCodes": list(self.course_codes or ()),
        }
        if self.due_date:
            payload["dueDate"] = self.due_date
        if self.submission_type:
            payload["assignmentType"] = self.submission_type
        return payload

    def describe(self) -> str:
        return (
            f"-> {self.path} -> contentUrl={self.content_url} name={self.name} "
            f"points={self.points} dueDate={self.due_date} "
            f"assignmentType={self.submission_type or 'unchanged/default'} "
            f"creatorUids={','.join(self.creator_uids or ())} "
            f"courseCodes={','.join(self.course_codes or ()) or 'none'}"
        )


def _text(value, field, path, report):
    """Scalar YAML values as stripped text; anything else is warned about and dropped."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (str, int, float, date)):
        return str(value).strip() or None
    report.warn(f"Ignoring non-text {field} {value!r}", path)
    return None


def _points(value, path, report):
    if value is None:
        return DEFAULT_POINTS
    try:
        if isinstance(value, bool):
            raise ValueError
        points = float(value)
        if math.isfinite(points) and points >= 0:
            return points
    except (TypeError, ValueError):
        pass
    report.warn(f"Invalid points {value!r}; using {DEFAULT_POINTS}", path)
    return DEFAULT_POINTS


def _creator_uids(fm, path, report):
    raw = fm.get("assignment_creator_uids")
    if raw is None:
        return None
    if not isinstance(raw, list) or not all(isinstance(uid, str) and uid.strip() for uid in raw) or not raw:
        report.warn(f"assignment_creator_uids must be a list of user ids, got {raw!r}; using defaults", path)
        return None
    return tuple(dict.fromkeys(uid.strip() for uid in raw))


def _course_codes(fm, path, report):
    # `courses` is a mapping whose values hold routing data (e.g. week); only keys matter here.
    raw = fm.get("courses")
    if raw is None:
        return None
    if not isinstance(raw, dict) or not all(isinstance(c, str) and c.strip() for c in raw) or not raw:
        report.warn(f"courses must be a mapping of course names, got {raw!r}; using defaults", path)
        return None
    return tuple(dict.fromkeys(course.strip().upper() for course in raw))


# ---------------------------------------------------------------- the catalog

class AssignmentCatalog:
    """All assignments in the repo, one per contentUrl."""

    def __init__(self, report: SyncReport):
        self.report = report
        self._by_url = {}
        self._conflicted = set()

    def scan(self, root: Path) -> "AssignmentCatalog":
        for path in find_pages(root):
            fm = read_frontmatter(path)
            if not fm or fm.get("assignment") is not True:
                continue
            try:
                self.add(Assignment.from_frontmatter(root, path, fm, self.report))
            except AssignmentDataError as error:
                self.report.skip(str(error), path)
        return self

    def add(self, assignment: Assignment):
        url = assignment.content_url
        if url in self._conflicted:
            return
        existing = self._by_url.get(url)
        if existing is None:
            self._by_url[url] = assignment
            return
        try:
            self._by_url[url] = existing.merge(assignment)
        except AssignmentDataError as error:
            # Neither copy is trustworthy; skip the URL without blocking the others.
            del self._by_url[url]
            self._conflicted.add(url)
            self.report.skip(str(error))

    def __iter__(self):
        return (assignment.with_defaults() for assignment in self._by_url.values())

    def __len__(self):
        return len(self._by_url)


# ---------------------------------------------------------------- Spring

class SpringClient:
    """Authenticated, rate-limited access to Spring's assignment API."""

    RETRY_ATTEMPTS = 3

    def __init__(self, base_url, requests_per_minute=80, session=None,
                 clock=time.monotonic, sleeper=time.sleep):
        if requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be greater than zero")
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.interval = 60.0 / requests_per_minute
        self.clock = clock
        self.sleeper = sleeper
        self._next_request_at = None

    def login(self, uid, password):
        response = self.session.post(
            f"{self.base_url}/authenticate", json={"uid": uid, "password": password}, timeout=20
        )
        if response.status_code != 200:
            raise RuntimeError(f"Authentication failed: {response.status_code} {response.text[:200]}")
        if "jwt_java_spring" not in self.session.cookies:
            raise RuntimeError("Authentication succeeded but the jwt cookie is missing")

    def upsert(self, assignment: Assignment):
        """Spring creates the assignment, or updates the one with the same contentUrl."""
        return self._post("/api/assignments/auto-create", data=assignment.to_payload(), timeout=30)

    def _post(self, route, **kwargs):
        response = None
        for attempt in range(self.RETRY_ATTEMPTS):
            self._wait_for_turn()
            response = self.session.post(f"{self.base_url}{route}", **kwargs)
            if response.status_code != 429 or attempt == self.RETRY_ATTEMPTS - 1:
                return response
            delay = _retry_after_seconds(response)
            print(f"Rate limited by Spring; retrying in {delay} seconds", file=sys.stderr)
            self.sleeper(delay)
        return response

    def _wait_for_turn(self):
        # Spacing requests keeps a full-repo sync under Spring's per-client limit.
        now = self.clock()
        if self._next_request_at is not None and now < self._next_request_at:
            self.sleeper(self._next_request_at - now)
            now = self._next_request_at
        self._next_request_at = now + self.interval


def _retry_after_seconds(response):
    try:
        return max(1, int(response.headers.get("Retry-After", "")))
    except ValueError:
        return 60


def is_page_rejection(status_code):
    """A 4xx about this page's data, as opposed to auth or rate-limit trouble."""
    return 400 <= status_code < 500 and status_code not in (401, 403, 429)


# ---------------------------------------------------------------- main

def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".")
    parser.add_argument("--base-url", default=os.getenv("BASE_URL", "https://spring.opencodingsociety.com"))
    parser.add_argument("--uid", default=os.getenv("PAGES_BOT_UID", "pages-bot"))
    parser.add_argument("--password", default=os.getenv("PAGES_BOT_PASSWORD", ""))
    parser.add_argument("--dry-run", action="store_true", help="Review only, even when a password is set")
    parser.add_argument("--requests-per-minute", type=int,
                        default=int(os.getenv("ASSIGNMENT_SYNC_REQUESTS_PER_MINUTE", "80")))
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Root not found: {root}", file=sys.stderr)
        return 2

    report = SyncReport()
    catalog = AssignmentCatalog(report).scan(root)
    print(f"Found {len(catalog)} assignments")

    dry_run = args.dry_run or not args.password
    client = None
    if dry_run:
        print("DRY RUN: no password provided or --dry-run set; Spring will not be contacted.")
    else:
        client = SpringClient(args.base_url, args.requests_per_minute)
        try:
            client.login(args.uid, args.password)
        except (RuntimeError, requests.RequestException) as error:
            report.error(str(error))
            return report.exit_code
        print(f"Authenticated as {args.uid}; writing to {args.base_url}")

    for assignment in catalog:
        print(assignment.describe())
        if client is None:
            continue
        try:
            response = client.upsert(assignment)
        except requests.RequestException as error:
            report.error(f"Could not reach Spring for '{assignment.content_url}': {error}")
            continue
        print(f"  {response.status_code} {response.text[:200]}")
        if response.ok:
            report.sent += 1
        elif is_page_rejection(response.status_code):
            report.skip(f"Spring rejected '{assignment.content_url}': {response.text[:200]}", assignment.path)
        else:
            report.error(f"Spring failed on '{assignment.content_url}': {response.status_code} {response.text[:200]}")

    print(report.summary(len(catalog)))
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
