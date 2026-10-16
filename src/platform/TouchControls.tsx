import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import { bus } from '../game/bus';

export function TouchControls() {
  const [show, setShow] = useState(false);
  const [leftPressed, setLeftPressed] = useState(false);
  const [rightPressed, setRightPressed] = useState(false);
  const [jumpFlash, setJumpFlash] = useState(false);

  useEffect(() => {
    const isTouch = 'ontouchstart' in window || (navigator.maxTouchPoints ?? 0) > 0;
    setShow(isTouch);
  }, []);

  if (!show) return null;

  const down = (k: 'left' | 'right' | 'jump') => bus.emit(`input:${k}:down`);
  const up = (k: 'left' | 'right' | 'jump') => bus.emit(`input:${k}:up`);

  return (
    <>
      <div style={leftGroup}>
        <button
          style={{
            ...dirBtn,
            transform: leftPressed ? 'scale(0.92)' : 'scale(1)',
            background: leftPressed ? 'linear-gradient(180deg, #dbeafe, #93c5fd)' : 'rgba(255,255,255,0.9)',
          }}
          onPointerDown={(e) => { e.preventDefault(); down('left'); setLeftPressed(true); }}
          onPointerUp={(e) => { e.preventDefault(); up('left'); setLeftPressed(false); }}
          onPointerLeave={() => { up('left'); setLeftPressed(false); }}
          onPointerCancel={() => { up('left'); setLeftPressed(false); }}
        >◀</button>

        <button
          style={{
            ...dirBtn,
            transform: rightPressed ? 'scale(0.92)' : 'scale(1)',
            background: rightPressed ? 'linear-gradient(180deg, #dbeafe, #93c5fd)' : 'rgba(255,255,255,0.9)',
          }}
          onPointerDown={(e) => { e.preventDefault(); down('right'); setRightPressed(true); }}
          onPointerUp={(e) => { e.preventDefault(); up('right'); setRightPressed(false); }}
          onPointerLeave={() => { up('right'); setRightPressed(false); }}
          onPointerCancel={() => { up('right'); setRightPressed(false); }}
        >▶</button>
      </div>

      <div style={jumpZone}
        onPointerDown={(e) => { e.currentTarget.setPointerCapture(e.pointerId); down('jump'); setJumpFlash(true); }}
        onPointerUp={(e) => { try { e.currentTarget.releasePointerCapture(e.pointerId); } catch {} up('jump'); setJumpFlash(false); }}
        onPointerCancel={() => { up('jump'); setJumpFlash(false); }}
      >
        <div style={{
          ...jumpCircle,
          transform: jumpFlash ? 'scale(0.9)' : 'scale(1)',
          background: jumpFlash
            ? 'linear-gradient(180deg, #ff7a2a, #d94e00)'
            : 'linear-gradient(180deg, #ff9a3c, #ff6b35)',
        }}>
          <span style={{ fontSize: 46, fontWeight: 900, color: '#fff', lineHeight: 1 }}>⤒</span>
          <span style={{ fontSize: 11, color: '#fff', fontWeight: 800, letterSpacing: 1.5, marginTop: 2 }}>JUMP</span>
        </div>
      </div>
    </>
  );
}

const leftGroup: CSSProperties = {
  position: 'fixed', bottom: 24, left: 20,
  display: 'flex', gap: 12, zIndex: 50, pointerEvents: 'none',
};
const dirBtn: CSSProperties = {
  width: 84, height: 84, borderRadius: '50%',
  color: '#1a3a6a', fontSize: 34, fontWeight: 900,
  border: '4px solid #ffffff',
  boxShadow: '0 6px 0 rgba(0,0,0,0.15), 0 10px 20px rgba(0,0,0,0.2)',
  display: 'grid', placeItems: 'center',
  pointerEvents: 'auto', touchAction: 'none',
  userSelect: 'none', WebkitUserSelect: 'none',
  padding: 0, transition: 'transform 0.08s ease, background 0.08s ease',
};
const jumpZone: CSSProperties = {
  position: 'fixed', right: 0, bottom: 0,
  width: '45%', height: '55%',
  zIndex: 45, touchAction: 'none',
  userSelect: 'none', WebkitUserSelect: 'none',
  display: 'flex', alignItems: 'flex-end', justifyContent: 'center',
  paddingBottom: 24, pointerEvents: 'auto',
};
const jumpCircle: CSSProperties = {
  width: 120, height: 120, borderRadius: '50%',
  display: 'flex', flexDirection: 'column',
  alignItems: 'center', justifyContent: 'center',
  border: '5px solid rgba(255,255,255,0.95)',
  boxShadow: '0 8px 0 rgba(180,60,0,0.55), 0 14px 28px rgba(0,0,0,0.3)',
  transition: 'transform 0.08s ease, background 0.08s ease',
  pointerEvents: 'none',
};
