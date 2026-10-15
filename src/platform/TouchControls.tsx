// src/platform/TouchControls.tsx
import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import { bus } from '../game/bus';

export function TouchControls() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const isTouch = 'ontouchstart' in window || (navigator.maxTouchPoints ?? 0) > 0;
    setShow(isTouch);
  }, []);

  if (!show) return null;

  const press = (k: 'left' | 'right' | 'jump') => bus.emit(`input:${k}:down`);
  const release = (k: 'left' | 'right' | 'jump') => bus.emit(`input:${k}:up`);

  return (
    <>
      <div style={leftGroup}>
        <button style={dirBtn}
          onPointerDown={() => press('left')}
          onPointerUp={() => release('left')}
          onPointerLeave={() => release('left')}
          onPointerCancel={() => release('left')}
        >◀</button>
        <button style={dirBtn}
          onPointerDown={() => press('right')}
          onPointerUp={() => release('right')}
          onPointerLeave={() => release('right')}
          onPointerCancel={() => release('right')}
        >▶</button>
      </div>
      <button style={jumpBtn}
        onPointerDown={() => press('jump')}
        onPointerUp={() => release('jump')}
        onPointerLeave={() => release('jump')}
        onPointerCancel={() => release('jump')}
      >⤒</button>
    </>
  );
}

const leftGroup: CSSProperties = {
  position: 'fixed', bottom: 24, left: 24,
  display: 'flex', gap: 12, zIndex: 50, pointerEvents: 'none',
};
const dirBtn: CSSProperties = {
  width: 84, height: 84, borderRadius: '50%',
  background: 'rgba(255,255,255,0.85)', color: '#1a3a6a',
  fontSize: 36, fontWeight: 900, border: '4px solid #fff',
  boxShadow: '0 6px 20px rgba(0,0,0,0.25)',
  display: 'grid', placeItems: 'center',
  pointerEvents: 'auto', touchAction: 'none', userSelect: 'none',
};
const jumpBtn: CSSProperties = {
  position: 'fixed', bottom: 24, right: 24,
  width: 110, height: 110, borderRadius: '50%',
  background: 'linear-gradient(180deg, #ff9a3c, #ff6b35)',
  color: '#fff', fontSize: 48, fontWeight: 900,
  border: '4px solid #fff',
  boxShadow: '0 6px 20px rgba(255,107,53,0.5)',
  display: 'grid', placeItems: 'center', zIndex: 50,
  pointerEvents: 'auto', touchAction: 'none', userSelect: 'none',
};
