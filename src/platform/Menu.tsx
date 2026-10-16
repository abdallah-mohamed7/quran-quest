import { progress } from '../game/progress';

export default function Menu({ onStart }: { onStart: () => void }) {
  return (
    <div style={{
      position: 'relative', width: '100%', height: '100vh',
      background: 'linear-gradient(180deg, #9cd4ff 0%, #c8e8ff 45%, #ffe5a8 100%)',
      display: 'grid', placeItems: 'center', overflow: 'hidden',
    }}>
      {/* Clouds */}
      <div style={{ position: 'absolute', top: '14%', left: '8%', width: 140, height: 42,
        background: 'rgba(255,255,255,0.85)', borderRadius: 40, boxShadow: '60px 10px 0 rgba(255,255,255,0.85)',
        animation: 'floaty 6s ease-in-out infinite' }} />
      <div style={{ position: 'absolute', top: '68%', left: '14%', width: 110, height: 36,
        background: 'rgba(255,255,255,0.8)', borderRadius: 40, boxShadow: '50px 8px 0 rgba(255,255,255,0.8)',
        animation: 'floaty 6s ease-in-out infinite 1.5s' }} />
      <div style={{ position: 'absolute', top: '24%', right: '10%', width: 150, height: 46,
        background: 'rgba(255,255,255,0.85)', borderRadius: 40, boxShadow: '70px 10px 0 rgba(255,255,255,0.85)',
        animation: 'floaty 6s ease-in-out infinite 0.7s' }} />

      {/* Content */}
      <div style={{ textAlign: 'center', padding: 24, zIndex: 10 }}>
        <div style={{ fontSize: 130, lineHeight: 1, animation: 'bob 2.4s ease-in-out infinite',
          filter: 'drop-shadow(0 12px 24px rgba(255,80,80,0.35))' }}>🎈</div>

        <h1 style={{
          fontSize: 'clamp(48px, 10vw, 92px)',
          margin: '12px 0 4px', letterSpacing: -1, fontWeight: 900,
          textShadow: '0 4px 0 rgba(255,255,255,0.9)',
        }}>
          <span style={{ color: '#ff6b35' }}>Quran</span>{' '}
          <span style={{ color: '#4a90e2' }}>Quest</span>
        </h1>

        <p className="ar" style={{
          fontSize: 'clamp(20px, 3vw, 30px)',
          margin: '8px 0 32px', color: '#3a5a8a', fontWeight: 700,
        }}>ارْكض · اقفِز · اسْتَمِع</p>

        <button onClick={onStart} style={{
          padding: '20px 52px',
          fontSize: 28, fontWeight: 800, color: '#fff',
          background: 'linear-gradient(180deg, #ff9a3c 0%, #ff6b35 100%)',
          borderRadius: 999,
          boxShadow: '0 6px 0 #c4451a, 0 12px 28px rgba(255,107,53,0.45)',
          display: 'inline-flex', alignItems: 'center', gap: 12,
        }}>
          <span>▶</span>
          <span>Let's Play!</span>
        </button>

        <p style={{ marginTop: 40, fontSize: 14, color: '#3a5a8a', opacity: 0.75, fontWeight: 600 }}>
          ← → move · SPACE jump · R restart
        </p>

        <button onClick={() => {
          if (window.confirm('Reset all stars and progress?')) {
            progress.clear();
            window.location.reload();
          }
        }} style={{
          marginTop: 18, padding: '8px 18px', fontSize: 14, fontWeight: 700,
          color: '#3a5a8a',
          background: 'rgba(255,255,255,0.7)',
          borderRadius: 999,
          border: '2px solid rgba(255,255,255,0.9)',
        }}>🔄 Reset progress</button>
      </div>
    </div>
  );
}
