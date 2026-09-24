---
layout: post
points: 1.0
categories: [Python, Nested-Conditionals]
lesson_language: Python
lesson_topic: Nested-Conditionals
lesson_part: interactive
lesson_source: APCSP
lesson_type: lesson
codemirror: true
microblog: true
assignment: true
assignment_name: 3.07 Nested Conditionals - Student Life
assignment_submission_type: code
assignment_creator_uids:
  - "jm1021"
  - "fred"
toc: true
comments: false
title: 3.07 Nested Conditionals
description: Learn nested conditionals through student accounts, homework, meals, and sports.
permalink: /python/nested-conditionals/student-life
---

# 3.7 Nested Conditionals in Python

A **nested conditional** is an `if` statement inside another `if`, `elif`, or `else` block. The outer decision chooses a path first, and the inner decision checks a more specific condition inside that path. This lesson uses one theme from start to finish: the accounts, homework, meals, and sports that shape a high school student's daily routine.

## 1. LxD Cycle Process

1. **Empathize:** A high school day contains decisions inside other decisions: account access before page permissions, homework before free time, lunch planning before practice, and practice before dinner. Nested conditionals can be confusing because indentation determines which decision owns each inner branch.

2. **Define:**
- **POV:** CSP students need familiar daily-life examples that make the outside-to-inside order of nested decisions visible.
- **Learning Goal:** Students will trace, write, test, and explain nested conditionals in a Python student-life dashboard.

3. **Ideate:**
- **HMW Question:** How might we turn a student's account, homework, meals, and sports schedule into clear nested decisions?
- **Activity:** Trace an after-school plan, repair an account check, test a lunch-and-practice decision, and build a daily routine dashboard.

4. **Prototype:** Build Tech Talk examples, three Popcorn Hacks, and one Homework Hack that all use the same student-life theme.

5. **Test:** Run every code runner with different account and schedule values, confirm each meaningful path, collect feedback, and record revisions in Section 5.

---

## 2. Lesson Plan

**Learning Objective:** Use nested `if` statements in Python when a student-life decision should happen only after an earlier account or schedule condition selects a path.

**Success Criteria:** You can trace a nested conditional, explain how indentation controls its branches, write a student-life decision with at least three outcomes, and test every meaningful path.

### Lesson Theme — High School Daily Life Dashboard

The lesson follows one student through a normal day:
- **Accounts:** log in before checking page permissions.
- **Homework:** check whether work is assigned before checking whether it is finished.
- **Meals:** plan lunch or a snack around the school and practice schedule.
- **Sports:** coordinate practice with homework and dinner.

### Tech Talk 1: Student Account Decisions

The outer condition is checked first. The inner condition is reached only when execution enters the block that contains it.

```python
has_account = True
password_correct = False

if has_account:
    if password_correct:
        print("Login approved")
    else:
        print("Incorrect password")
else:
    print("Create an account first")
```

Python checks `has_account` before it checks `password_correct`. If `has_account` is `False`, the password condition is skipped because it belongs inside the first branch.

### Tech Talk 2: Homework Before Dinner

Python uses indentation to show which statements belong together. Here, the program checks whether homework exists before deciding whether the student can move on to dinner or free time.

```python
homework_assigned = True
homework_finished = False

if homework_assigned:
    if homework_finished:
        print("Homework finished — time for dinner")
    else:
        print("Finish homework before dinner")
else:
    print("No homework tonight — check tomorrow's schedule")
```

This homework example has three possible paths, but only one message prints during a run. Moving the inner `else` to the wrong indentation level would change which `if` statement it belongs to.

### Tech Talk 3: Nested and Compound Conditions Are Different

A compound condition checks multiple Boolean expressions at the same time. A nested conditional makes the second check depend on the first path.

| Purpose | Python example |
| --- | --- |
| Both rules must be true for one result | `if practice_today and homework_finished:` |
| Check homework only when practice is scheduled | `if practice_today:` then nested `if homework_finished:` |

The same nested structure appears in three forms:

| Form | Outer and inner decision |
| --- | --- |
| Python | `if condition_a:` then indented `if condition_b:` |
| JavaScript | `if (conditionA) { if (conditionB) { ... } }` |
| College Board pseudocode | `IF(conditionA) { IF(conditionB) { ... } }` |

---

## 3. Popcorn Hacks & Practice Tasks

### Popcorn Hack 1: After-School Homework Plan (Beginner)

Start by tracing completed code. Predict whether the student gets free time, must finish homework, or follows a weekend plan. Then run the code and test every path.

{% capture challenge0 %}
Popcorn Hack 1 - Test the after-school homework plan
{% endcapture %}

{% capture code0 %}
is_weekday = True
homework_finished = False

if is_weekday:
    if homework_finished:
        print("Free time")
    else:
        print("Finish homework")
else:
    print("Weekend plan")
{% endcapture %}

{% capture source0 %}
```python
# CODE_RUNNER: Popcorn Hack 1 - Test the after-school homework plan

is_weekday = True
homework_finished = False

if is_weekday:
    if homework_finished:
        print("Free time")
    else:
        print("Finish homework")
else:
    print("Weekend plan")
```
{% endcapture %}

{% include runners/code.html
   runner_id="python-nested-conditionals-student-life-0"
   language="python"
   challenge=challenge0
   code=code0
   source=source0
%}

Do these three things:
1. Write the message that will print.
2. Name the outer branch and inner branch the program follows.
3. Change the values to reach each of the other two outcomes.

### Popcorn Hack 2: Repair the Student Account Check (Intermediate)

Next, debug existing code. The student dashboard should check `has_permission` only after the student logs in, but the permission decision is not indented correctly.

{% capture challenge1 %}
Popcorn Hack 2 - Repair the student account check
{% endcapture %}

{% capture code1 %}
logged_in = True
has_permission = False

if logged_in:
    print("Account found")
if has_permission:
    print("Page opened")
else:
    print("Permission needed")
{% endcapture %}

{% capture source1 %}
```python
# CODE_RUNNER: Popcorn Hack 2 - Repair the student account check

logged_in = True
has_permission = False

if logged_in:
    print("Account found")
if has_permission:
    print("Page opened")
else:
    print("Permission needed")
```
{% endcapture %}

{% include runners/code.html
   runner_id="python-nested-conditionals-student-life-1"
   language="python"
   challenge=challenge1
   code=code1
   source=source1
%}

Do these four things:
1. Explain why the current code is not nested.
2. Move the permission check inside the logged-in branch.
3. Add an outer `else` that prints `Log in first`.
4. Test all three possible messages.

### Popcorn Hack 3: Lunch and Sports Practice (Advanced)

Now complete a partial solution. A student needs to plan lunch and decide whether to bring an extra snack for after-school practice. Add the missing inner decisions, test all four paths, and then translate the finished structure.

{% capture challenge2 %}
Popcorn Hack 3 - Test the lunch and sports-practice plan
{% endcapture %}

{% capture code2 %}
lunch_packed = True
practice_after_school = True

if lunch_packed:
    # TODO: Add a nested conditional that checks practice_after_school.
    pass
else:
    # TODO: Add another nested conditional that checks practice_after_school.
    pass
{% endcapture %}

{% capture source2 %}
```python
# CODE_RUNNER: Popcorn Hack 3 - Test the lunch and sports-practice plan

lunch_packed = True
practice_after_school = True

if lunch_packed:
    # TODO: Add a nested conditional that checks practice_after_school.
    pass
else:
    # TODO: Add another nested conditional that checks practice_after_school.
    pass
```
{% endcapture %}

{% include runners/code.html
   runner_id="python-nested-conditionals-student-life-2"
   language="python"
   challenge=challenge2
   code=code2
   source=source2
%}

Your completed code should print four different recommendations: packed lunch with practice, packed lunch without practice, buying lunch with practice, and buying lunch without practice. Change both values to test all four outcomes. Then write the same structure in JavaScript and College Board pseudocode and explain which condition is checked first.

### Homework Hack: High School Daily Routine Dashboard

Write your own Python nested conditional from scratch to guide a student through an ordinary school day. The starter runner gives you only the student-life data; you must design the complete decision structure yourself. Your dashboard should combine account access, homework, meals, and sports practice.

Your finished program must:
1. store at least four student-life values, including login status, homework status, a meal decision, and sports-practice status,
2. use an outer account `if` / `else` before checking the student's schedule,
3. contain at least two nested decisions,
4. produce at least four clear recommendations,
5. test inputs that reach every meaningful outcome,
6. include 2–3 sentences explaining why the inner checks depend on the outer decisions.

> **Submission:** Use the runner below to build and test your dashboard. When it works, **scroll to the end of this page** to write or paste your final Python code into the Code Submission form and submit it.

{% capture challenge3 %}
Homework Hack - Build a high school daily routine dashboard
{% endcapture %}

{% capture code3 %}
student = {
    "logged_in": True,
    "homework_finished": False,
    "lunch_packed": True,
    "practice_today": True
}

# Write your complete nested conditional below.
# Do not delete the starter data. Test several value combinations.
{% endcapture %}

{% capture source3 %}
```python
# CODE_RUNNER: Homework Hack - Build a high school daily routine dashboard

student = {
    "logged_in": True,
    "homework_finished": False,
    "lunch_packed": True,
    "practice_today": True
}

# Write your complete nested conditional below.
# Do not delete the starter data. Test several value combinations.
```
{% endcapture %}

{% include runners/code.html
   runner_id="python-nested-conditionals-student-life-3"
   language="python"
   challenge=challenge3
   code=code3
   source=source3
%}

---

## 4. Grading Plan (1 Point Total)

| Activity | Points | What earns the points |
| --- | ---: | --- |
| Popcorn Hack 1 | 0.15 | Correctly trace and test all after-school homework outcomes. |
| Popcorn Hack 2 | 0.15 | Correctly nest the account permission check and test all login outcomes. |
| Popcorn Hack 3 | 0.20 | Complete and test all lunch/practice paths, translate the structure, and explain the execution order. |
| Homework Hack | 0.50 | Independently write and submit a working student-life dashboard covering accounts, homework, meals, and sports; test all outcomes and explain the nesting. |
| **Total** | **1.0** | |

---

## 5. Lesson Revisions & Feedback Evidence

- Kept the numbered `1` through `5` lesson structure used by the Boolean Expressions and Random Values lessons.
- Unified every Tech Talk and hack around one high-school daily-life theme: accounts, homework, meals, and sports.
- Increased difficulty from tracing completed code, to debugging indentation, to completing a partial nested structure, to independently writing the Homework Hack.
- Added assignment metadata so the page provides a code-submission form.
- Changed the permalink to `/python/nested-conditionals/student-life` to prevent a collision with another team's lesson.
- Enabled the table of contents for faster navigation.
- **Feedback applied:** Added a clear instruction telling students to scroll to the bottom of the page to write or paste and submit their final Homework Hack code.

---

## Submit Your Homework

Scroll to the **Code Submission** form directly below this lesson. Choose **Python**, write or paste only your final Homework Hack code, add short testing notes, and submit. Do not paste Markdown code fences.
