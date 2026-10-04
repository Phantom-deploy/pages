import { createAssetCatalog } from './asset-catalog.mjs';
import { createDefaultBuilderState } from './builder-state.mjs';
import { generateLevelCode } from './code-generator.mjs';
import { waitForGameRunner } from './runner-bridge.mjs';

const root = document.querySelector('[data-gamebuilder-workbench]');
if (!root) {
  throw new Error('GameBuilder workbench root was not found');
}

const status = root.querySelector('[data-role="status"]');
const builderPanel = root.querySelector('[data-role="builder-panel"]');
const workspace = root.querySelector('[data-role="workspace"]');
const collapseButton = root.querySelector('[data-action="toggle-builder"]');
const form = root.querySelector('[data-role="builder-form"]');
const generateButton = root.querySelector('[data-action="generate"]');

function setStatus(message, state = 'info') {
  status.textContent = message;
  status.dataset.state = state;
}

function siteUrl(path) {
  return `${root.dataset.baseUrl || ''}${path}`;
}

async function fetchManifest(url, label) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Could not load ${label} manifest (${response.status})`);
  }
  const manifest = await response.json();
  if (!Array.isArray(manifest)) {
    throw new TypeError(`${label} manifest must contain a JSON array`);
  }
  return manifest;
}

function populateSelect(select, entries) {
  select.replaceChildren();
  for (const entry of entries.values()) {
    const option = document.createElement('option');
    option.value = entry.key;
    option.textContent = entry.name;
    select.append(option);
  }
}

function readForm(state) {
  return {
    ...state,
    name: form.elements.namedItem('game-name').value,
    backgroundKey: form.elements.namedItem('background').value,
    player: {
      ...state.player,
      name: form.elements.namedItem('player-name').value,
      spriteKey: form.elements.namedItem('player-sprite').value,
      position: {
        x: Number(form.elements.namedItem('player-x').value),
        y: Number(form.elements.namedItem('player-y').value)
      }
    }
  };
}

function fillForm(state) {
  form.elements.namedItem('game-name').value = state.name;
  form.elements.namedItem('background').value = state.backgroundKey;
  form.elements.namedItem('player-name').value = state.player.name;
  form.elements.namedItem('player-sprite').value = state.player.spriteKey;
  form.elements.namedItem('player-x').value = String(state.player.position.x);
  form.elements.namedItem('player-y').value = String(state.player.position.y);
}

collapseButton.addEventListener('click', () => {
  const expanded = collapseButton.getAttribute('aria-expanded') === 'true';
  collapseButton.setAttribute('aria-expanded', String(!expanded));
  collapseButton.textContent = expanded ? 'Show builder' : 'Hide builder';
  builderPanel.hidden = expanded;
  workspace.classList.toggle('is-builder-collapsed', expanded);
});

try {
  const [backgroundManifest, spriteManifest, runner] = await Promise.all([
    fetchManifest(siteUrl('/images/projects/gamebuilder/bg/index.json'), 'Background'),
    fetchManifest(siteUrl('/images/projects/gamebuilder/sprites/index.json'), 'Sprite'),
    waitForGameRunner('gamebuilder-v2')
  ]);
  const catalog = createAssetCatalog(backgroundManifest, spriteManifest);
  populateSelect(form.elements.namedItem('background'), catalog.backgrounds);
  populateSelect(form.elements.namedItem('player-sprite'), catalog.sprites);

  const firstBackground = catalog.backgrounds.keys().next().value;
  const defaultSprite = catalog.sprites.has('chill_guy')
    ? 'chill_guy'
    : catalog.sprites.keys().next().value;
  let state = createDefaultBuilderState(firstBackground, defaultSprite);
  let lastGeneratedCode = '';
  fillForm(state);

  form.addEventListener('input', () => {
    state = readForm(state);
    setStatus('Builder settings changed. Generate code to sync them to GAME_RUNNER.');
  });
  form.addEventListener('change', () => {
    state = readForm(state);
    setStatus('Builder settings changed. Generate code to sync them to GAME_RUNNER.');
  });

  generateButton.addEventListener('click', () => {
    state = readForm(state);
    const result = generateLevelCode(state, catalog);
    if (result.errors.length > 0) {
      setStatus(result.errors.map((error) => error.message).join(' '), 'error');
      return;
    }

    const currentCode = runner.getCode();
    if (currentCode.trim() && currentCode !== lastGeneratedCode) {
      const confirmed = window.confirm('Replace the code currently in GAME_RUNNER with generated code?');
      if (!confirmed) return;
    }
    runner.setCode(result.code);
    lastGeneratedCode = result.code;
    setStatus('Generated code is synced to GAME_RUNNER. Use its Run button to play.');
  });

  if (runner.getCode().trim()) {
    setStatus('Existing GAME_RUNNER code was preserved. Choose Generate / Sync Code when ready to replace it.');
  } else {
    generateButton.click();
  }
} catch (error) {
  console.error('GameBuilder workbench initialization failed:', error);
  setStatus(error.message || 'GameBuilder could not initialize.', 'error');
}
