// src/game/PhaserGame.tsx
import { useEffect, useRef } from 'react';
import Phaser from 'phaser';
import { BootScene } from './scenes/BootScene';
import { LevelScene } from './scenes/LevelScene';
import { bus, state } from './bus';
import type { LevelDef } from './types';

export default function PhaserGame({ level }: { level: LevelDef }) {
  const hostRef = useRef<HTMLDivElement>(null);
  const gameRef = useRef<Phaser.Game | null>(null);

  useEffect(() => {
    if (!hostRef.current || gameRef.current) return;

    const parent = hostRef.current;
    const w = parent.clientWidth  || window.innerWidth;
    const h = parent.clientHeight || window.innerHeight;

    gameRef.current = new Phaser.Game({
      type: Phaser.AUTO,
      parent,
      width: w,
      height: h,
      backgroundColor: '#c8e8ff',
      antialias: true,
      pixelArt: false,
      roundPixels: false,
      physics: {
        default: 'arcade',
        arcade: { gravity: { x: 0, y: 1000 }, debug: false },
      },
      scale: {
        mode: Phaser.Scale.RESIZE,     // ← canvas matches parent exactly
        autoCenter: Phaser.Scale.CENTER_BOTH,
        width: '100%',
        height: '100%',
      },
      scene: [BootScene, LevelScene],
    });

    // Keep canvas matched on resize / rotation
    const onResize = () => {
      gameRef.current?.scale.resize(parent.clientWidth, parent.clientHeight);
    };
    window.addEventListener('resize', onResize);
    window.addEventListener('orientationchange', onResize);

    return () => {
      window.removeEventListener('resize', onResize);
      window.removeEventListener('orientationchange', onResize);
      gameRef.current?.destroy(true);
      gameRef.current = null;
    };
  }, []);

  useEffect(() => {
    state.currentLevel = level;
    const t = window.setTimeout(() => bus.emit('level:load', level), 0);
    return () => window.clearTimeout(t);
  }, [level]);

  return (
    <div
      ref={hostRef}
      style={{
        width: '100%',
        height: '100%',
        overflow: 'hidden',
      }}
    />
  );
}
