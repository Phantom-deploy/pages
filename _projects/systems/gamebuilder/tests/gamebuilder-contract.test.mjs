import test from 'node:test';
import assert from 'node:assert/strict';
import { createAssetCatalog } from '../js/asset-catalog.mjs';
import { createDefaultBuilderState, validateBuilderState } from '../js/builder-state.mjs';
import { generateLevelCode } from '../js/code-generator.mjs';

const catalog = createAssetCatalog(
  [{ name: 'Alien Planet', src: 'alien_planet.jpg' }],
  [{
    name: 'Chill Guy',
    src: 'chillguy.png',
    rows: 4,
    cols: 3,
    scaleFactor: 5,
    movementPreset: 'four-row-8way'
  }]
);

test('builds a versioned default document with the selected assets', () => {
  const state = createDefaultBuilderState('alien_planet', 'chill_guy');
  assert.equal(state.schemaVersion, 1);
  assert.deepEqual(validateBuilderState(state, catalog), []);
});

test('rejects unknown assets and out-of-range positions', () => {
  const state = createDefaultBuilderState('missing', 'chill_guy');
  state.player.position.x = 1.5;
  const fields = validateBuilderState(state, catalog).map((error) => error.field);
  assert.deepEqual(fields, ['backgroundKey', 'player.position.x']);
});

test('generates GAME_RUNNER-compatible source with safe string literals', () => {
  const state = createDefaultBuilderState('alien_planet', 'chill_guy');
  state.name = "Ada's Adventure";
  state.player.name = 'Player One';
  const result = generateLevelCode(state, catalog);
  assert.deepEqual(result.errors, []);
  assert.match(result.code, /export const gameLevelClasses = \[GameLevelBuilder\]/);
  assert.match(result.code, /export \{ GameControl \}/);
  assert.match(result.code, /Ada's Adventure/);
  assert.match(result.code, /\/images\/projects\/gamebuilder\/bg\/alien_planet\.jpg/);
  assert.match(result.code, /\/images\/projects\/gamebuilder\/sprites\/chillguy\.png/);
});

test('rejects malformed sprite manifests instead of generating incomplete code', () => {
  assert.throws(() => createAssetCatalog(
    [{ name: 'Background', src: 'background.jpg' }],
    [{ name: 'Broken sprite', src: '../sprite.png', rows: 4, cols: 3, scaleFactor: 5, movementPreset: 'four-row-8way' }]
  ), /invalid name or source path/);
});
