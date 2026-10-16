import levels from '../game/levels';
import { progress } from '../game/progress';

const GRADIENTS = [
  'linear-gradient(180deg, #ff8585, #e63946)',
  'linear-gradient(180deg, #ffb066, #e85d04)',
  'linear-gradient(180deg, #ffd966, #b8860b)',
  'linear-gradient(180deg, #a8e063, #56ab2f)',
  'linear-gradient(180deg, #6ee7b7, #059669)',
  'linear-gradient(180deg, #7dd3fc, #0284c7)',
  'linear-gradient(180deg, #a78bfa, #7c3aed)',
  'linear-gradient(180deg, #f0abfc, #c026d3)',
  'linear-gradient(180deg, #fda4af, #e11d48)',
  'linear-gradient(180deg, #fdba74, #ea580c)',
];
const SHADOW = [
  '#991b1b', '#9a3412', '#78350f', '#14532d', '#064e3b',
  '#075985', '#4c1d95', '#701a75', '#881337', '#7c2d12',
];

export default function LevelSelect({
  onPick, onBack,
}: { onPick: (id: string) => void; onBack: () => void }) {
  return (
    <div style={{
      minHeight: '100vh', width: '100%', overflowY: 'auto',
      background: 'linear-gradient(180deg, #9cd4ff 0%, #c8e8ff 60%, #d8f5c0 100%)',
      padding: '32px 20px 80px',
    }}>
      <div style={{ maxWidth: 820, margin: '0 auto' }}>
        <header style={{ textAlign: 'center', marginBottom: 32 }}>
          <h1 className="ar" style={{
            fontSize: 'clamp(36px, 6vw, 56px)', margin: 0,
            color: '#1a3a6a', fontWeight: 900,
            textShadow: '0 3px 0 rgba(255,255,255,0.85)',
          }}>اختر مرحلة</h1>
          <p style={{ fontSize: 18, color: '#4a6a9a', margin: '6px 0 0', fontWeight: 600 }}>
            Choose your adventure
          </p>
        </header>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
          gap: 20,
        }}>
          {levels.map((lvl, i) => {
            const p = progress.get(lvl.id);
            const stars = p?.stars ?? 0;
            const best = p?.bestTimeMs;
            return (
              <button key={lvl.id} onClick={() => onPick(lvl.id)} style={{
                position: 'relative',
                aspectRatio: '1 / 1',
                borderRadius: 24,
                border: '4px solid rgba(255,255,255,0.95)',
                background: GRADIENTS[i % 10],
                boxShadow: `0 8px 0 ${SHADOW[i % 10]}, 0 14px 26px rgba(0,0,0,0.14)`,
                padding: 14,
                display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center', gap: 6,
                fontFamily: 'inherit',
                transition: 'transform 0.15s ease',
              }}>
                <span style={{
                  position: 'absolute', top: -12, left: -12,
                  width: 40, height: 40, borderRadius: '50%',
                  background: '#fff', color: '#1a3a6a',
                  display: 'grid', placeItems: 'center',
                  fontWeight: 900, fontSize: 18,
                  boxShadow: '0 3px 8px rgba(0,0,0,0.2)',
                }}>{i + 1}</span>

                <div className="ar" style={{
                  fontSize: 18, fontWeight: 900, color: '#fff',
                  textAlign: 'center', lineHeight: 1.2,
                  textShadow: '0 2px 4px rgba(0,0,0,0.35)',
                  padding: '0 4px',
                }}>{lvl.name}</div>

                <div style={{ fontSize: 20, letterSpacing: 2, marginTop: 2 }}>
                  {[0, 1, 2].map(s => (
                    <span key={s} style={{ opacity: s < stars ? 1 : 0.28 }}>⭐</span>
                  ))}
                </div>

                {best !== undefined && (
                  <div style={{ fontSize: 11, color: '#fff', fontWeight: 700, opacity: 0.95 }}>
                    ⏱ {(best / 1000).toFixed(1)}s
                  </div>
                )}
              </button>
            );
          })}
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', marginTop: 40 }}>
          <button onClick={onBack} style={{
            padding: '14px 32px', fontSize: 20, fontWeight: 800, color: '#1a3a6a',
            background: '#fff', borderRadius: 999,
            boxShadow: '0 6px 0 #b8d0e0',
            display: 'flex', alignItems: 'center', gap: 8,
          }}>
            <span>←</span>
            <span className="ar">رجوع</span>
          </button>
        </div>
      </div>
    </div>
  );
}
