export function createDefaultBuilderState(backgroundKey, spriteKey) {
  if (!backgroundKey || !spriteKey) {
    throw new TypeError('A background and player sprite are required');
  }

  return {
    schemaVersion: 1,
    name: 'My Game',
    backgroundKey,
    player: {
      name: 'Player',
      spriteKey,
      position: { x: 0.5, y: 0.8 }
    }
  };
}

export function validateBuilderState(state, catalog) {
  const errors = [];
  if (!state || state.schemaVersion !== 1) {
    errors.push({ field: 'document', message: 'Unsupported builder document version.' });
    return errors;
  }

  if (typeof state.name !== 'string' || !state.name.trim()) {
    errors.push({ field: 'name', message: 'Enter a game name.' });
  }
  if (!catalog.backgrounds.has(state.backgroundKey)) {
    errors.push({ field: 'backgroundKey', message: 'Choose an available background.' });
  }
  if (!state.player || typeof state.player.name !== 'string' || !state.player.name.trim()) {
    errors.push({ field: 'player.name', message: 'Enter a player name.' });
  }
  if (!catalog.sprites.has(state.player?.spriteKey)) {
    errors.push({ field: 'player.spriteKey', message: 'Choose an available player sprite.' });
  }

  for (const axis of ['x', 'y']) {
    const value = state.player?.position?.[axis];
    if (!Number.isFinite(value) || value < 0 || value > 1) {
      errors.push({
        field: `player.position.${axis}`,
        message: `Player ${axis.toUpperCase()} position must be between 0 and 1.`
      });
    }
  }

  return errors;
}
