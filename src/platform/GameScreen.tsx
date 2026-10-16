import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import PhaserGame from '../game/PhaserGame';
import { bus } from '../game/bus';
import { quranAudio } from '../game/systems/QuranAudio';
import type { Ayah, LevelDef, LevelResult, Theme } from '../game/types';
import { TouchControls } from './TouchControls';
import { progress, computeStars } from '../game/progress';

type CoinPayload = { got: number; total: number };

const THEME_SKY: Record<Theme, { top: string; bottom: string }> = {
  day:    { top: '#9cd4ff', bottom: '#dff0ff' },
  sunset: { top: '#ffc6a8', bottom: '#ffe8d0' },
  forest: { top: '#b8e8d8', bottom: '#e8f8f0' },
  candy:  { top: '#ffd0e8', bottom: '#fff4fa' },
  ocean:  { top: '#9cd4ff', bottom: '#e8f6ff' },
};

const AYAH_COUNTS: Record<number, number> = {
  105: 5, 106: 4, 107: 7, 108: 3, 109: 6,
  110: 3, 111: 5, 112: 4, 113: 5, 114: 6,
};

export default function GameScreen({
  level, onExit, onNext, hasNext,
}: {
  level: LevelDef; onExit: () => void; onNext: () => void; hasNext: boolean;
}) {
  const [currentAyah, setCurrentAyah] = useState<Ayah | null>(null);
  const [result, setResult] = useState<LevelResult | null>(null);
  const [paused, setPaused] = useState(false);
  const [stars, setStars] = useState(0);
  const [coins, setCoins] = useState<CoinPayload>({ got: 0, total: 0 });

  const sky = THEME_SKY[level.theme];

  useEffect(() => {
    const count = AYAH_COUNTS[level.surah] ?? 1;
    const q: Ayah[] = [];
    for (let a = 1; a <= count; a++) {
      q.push({
        surah: level.surah,
        ayah: a,
        file: `quran/audio/surahs/${String(level.surah).padStart(3, '0')}/${String(a).padStart(3, '0')}.mp3`,
      });
    }
    quranAudio.load(q);
    void quranAudio.start();

    const onAyah = (e: Event) => setCurrentAyah((e as CustomEvent<Ayah>).detail);
    const onPlay = () => setPaused(false);
    const onPause = () => setPaused(true);

    quranAudio.addEventListener('ayah', onAyah);
    quranAudio.addEventListener('play', onPlay);
    quranAudio.addEventListener('pause', onPause);
    return () => {
      quranAudio.removeEventListener('ayah', onAyah);
      quranAudio.removeEventListener('play', onPlay);
      quranAudio.removeEventListener('pause', onPause);
      quranAudio.pause();
    };
  }, [level]);

  useEffect(() => {
    setResult(null); setStars(0); setCoins({ got: 0, total: 0 });
  }, [level.id]);

  useEffect(() => {
    const onWin = (r: LevelResult) => {
      const s = computeStars(r.coinsCollected, r.coinsTotal, r.timeMs);
      progress.record(r.levelId, s, r.timeMs, r.coinsCollected);
      setStars(s); setResult(r); quranAudio.pause();
    };
    const onCoins = (...args: unknown[]) => {
      const f = args[0];
      if (f && typeof f === 'object' && 'got' in (f as object)) {
        const p = f as CoinPayload;
        setCoins({ got: p.got, total: p.total });
      }
    };
    bus.on('level:win', onWin);
    bus.on('coins:update', onCoins);
    return () => { bus.off('level:win', onWin); bus.off('coins:update', onCoins); };
  }, []);

  const toggleAudio = () => {
    if (paused) void quranAudio.resume();
    else quranAudio.pause();
  };

  return (
    <div style={{
      display: 'grid', gridTemplateRows: '1fr',
      height: '100vh', width: '100%',
      background: `linear-gradient(180deg, ${sky.top} 0%, ${sky.bottom} 100%)`,
    }}>
      <div style={{ position: 'relative', overflow: 'hidden', width: '100%', height: '100%' }}>
        <PhaserGame level={level} />
        <TouchControls />

        {currentAyah && (
          <div style={{ ...pill, top: 12, left: 12 }}>
            <span style={{ fontWeight: 800 }}>{currentAyah.surah}:{currentAyah.ayah}</span>
          </div>
        )}

        <div style={{ ...pill, top: 12, left: '50%', transform: 'translateX(-50%)' }}>
          🪙 <span style={{ fontWeight: 800 }}>{coins.got}/{coins.total}</span>
        </div>

        <div className="ar" style={{
          ...pill, top: 12, right: 12,
          maxWidth: '46vw', direction: 'rtl', fontSize: 14,
        }}>
          <span style={{ fontWeight: 800 }}>{level.name}</span>
        </div>

        <button onClick={toggleAudio} style={{
          ...circleBtn, position: 'absolute', bottom: 14, left: 14,
        }}>{paused ? '▶' : '⏸'}</button>

        <button onClick={onExit} style={{
          ...circleBtn, position: 'absolute', bottom: 14, right: 14,
        }}>✕</button>

        {result && (
          <div style={overlay}>
            <div style={celebration}>
              <div style={{ fontSize: 80, lineHeight: 1, marginBottom: 6 }}>🏆</div>
              <h2 style={winTitle}>Level Complete!</h2>
              <div style={{ fontSize: 56, marginTop: 4, letterSpacing: 8 }}>
                {[0, 1, 2].map(i => (
                  <span key={i} style={{ opacity: i < stars ? 1 : 0.18 }}>⭐</span>
                ))}
              </div>
              <p className="ar" style={winSub}>أحسنت!</p>
              <p style={winTime}>
                ⏱ {(result.timeMs / 1000).toFixed(1)}s · 🪙 {result.coinsCollected}/{result.coinsTotal}
              </p>
              <div style={btnRow}>
                {hasNext && (
                  <button onClick={() => { setResult(null); onNext(); }}
                    style={{ ...bigBtn, background: 'linear-gradient(180deg, #69db7c, #37b24d)' }}>
                    ▶ Next
                  </button>
                )}
                <button onClick={() => { setResult(null); void quranAudio.resume(); }}
                  style={{ ...bigBtn, background: 'linear-gradient(180deg, #4dabf7, #1c7ed6)' }}>
                  🔁 Replay
                </button>
                <button onClick={onExit}
                  style={{ ...bigBtn, background: 'linear-gradient(180deg, #ffa94d, #e8590c)' }}>
                  🏠 Menu
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const pill: CSSProperties = {
  position: 'absolute', padding: '8px 14px', borderRadius: 999,
  background: 'rgba(255,255,255,0.92)', color: '#1a3a6a',
  fontSize: 14, fontWeight: 700,
  boxShadow: '0 3px 10px rgba(0,0,0,0.15)',
  display: 'flex', alignItems: 'center', gap: 6, pointerEvents: 'none',
};
const circleBtn: CSSProperties = {
  width: 48, height: 48, borderRadius: '50%',
  background: 'rgba(255,255,255,0.92)', color: '#1a3a6a',
  fontSize: 20, fontWeight: 800,
  boxShadow: '0 3px 10px rgba(0,0,0,0.2)',
  display: 'grid', placeItems: 'center', zIndex: 40,
};
const overlay: CSSProperties = {
  position: 'absolute', inset: 0, display: 'grid', placeItems: 'center',
  background: 'rgba(20,40,80,0.55)', backdropFilter: 'blur(8px)', zIndex: 100,
};
const celebration: CSSProperties = {
  position: 'relative', textAlign: 'center',
  padding: '36px 44px 28px',
  background: 'linear-gradient(180deg, #ffffff 0%, #f0f8ff 100%)',
  borderRadius: 32, border: '6px solid #ffd166',
  boxShadow: '0 20px 60px rgba(0,0,0,0.4)', maxWidth: '90vw',
  animation: 'popIn 0.4s ease-out',
};
const winTitle: CSSProperties = {
  fontSize: 36, fontWeight: 900, margin: '8px 0 4px', color: '#1a3a6a',
};
const winSub: CSSProperties = {
  fontSize: 22, color: '#4a6a9a', fontWeight: 700, margin: '4px 0 12px',
};
const winTime: CSSProperties = {
  fontSize: 17, color: '#8a6a3a', fontWeight: 700, marginBottom: 20,
};
const btnRow: CSSProperties = {
  display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap',
};
const bigBtn: CSSProperties = {
  padding: '14px 24px', fontSize: 18, fontWeight: 800,
  color: '#fff', border: 'none', borderRadius: 18,
  cursor: 'pointer', fontFamily: 'inherit',
};
