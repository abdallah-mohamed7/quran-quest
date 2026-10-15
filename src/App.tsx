// src/App.tsx
import { useState } from 'react';
import Menu from './platform/Menu';
import LevelSelect from './platform/LevelSelect';
import GameScreen from './platform/GameScreen';
import levels from './game/levels';
import type { LevelDef } from './game/types';

type Screen = 'menu' | 'select' | 'playing';

export default function App() {
  const [screen, setScreen] = useState<Screen>('menu');
  const [levelIndex, setLevelIndex] = useState(0);
  const level: LevelDef = levels[levelIndex];

  const nextLevel = () => setLevelIndex(i => (i + 1) % levels.length);

  return (
    <div style={{ width: '100%', height: '100vh', overflow: 'hidden' }}>
      {screen === 'menu' && (
        <Menu onStart={() => setScreen('select')} />
      )}
      {screen === 'select' && (
        <LevelSelect
          onPick={(id) => {
            const idx = levels.findIndex(l => l.id === id);
            setLevelIndex(idx === -1 ? 0 : idx);
            setScreen('playing');
          }}
          onBack={() => setScreen('menu')}
        />
      )}
      {screen === 'playing' && (
        <GameScreen
          key={level.id}
          level={level}
          onExit={() => setScreen('select')}
          onNext={nextLevel}
          hasNext={levelIndex < levels.length - 1}
        />
      )}
    </div>
  );
}
