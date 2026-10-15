// src/platform/GameScreen.tsx
import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import PhaserGame from '../game/PhaserGame';
import { bus } from '../game/bus';
import { quranAudio } from '../game/systems/QuranAudio';
import { TouchControls } from './TouchControls';
import { progress, computeStars } from '../game/progress';
import type { LevelDef, LevelResult, PageAudio, Theme } from '../game/types';

type CoinPayload = { got: number; total: number };

// Sky colors — used both on the game canvas AND the container behind it.
// This is why bars will vanish: they match the sky.
const THEME_SKY: Record<Theme, { top: string; bottom: string }> = {
  day:    { top: '#4aa8ff', bottom: '#c8e8ff' },
  sunset: { top: '#ff8866', bottom: '#ffd8a0' },
  forest: { top: '#6ac8a8', bottom: '#d8f0e8' },
  candy:  { top: '#ff8ac8', bottom: '#ffe0f0' },
  ocean:  { top: '#4ac8ff', bottom: '#d0f0ff' },
};

export default function GameScreen({
  level,
  onExit,
  onNext,
  hasNext,
}: {
  level: LevelDef;
  onExit: () => void;
  onNext: () => void;
  hasNext: boolean;
}) {
  const [currentPage, setCurrentPage] = useState<PageAudio | null>(null);
  const [result, setResult] = useState<LevelResult | null>(null);
  const [paused, setPaused] = useState(false);
  const [stars, setStars] = useState(0);
  const [coins, setCoins] = useState<CoinPayload>({ got: 0, total: 0 });

  const theme = level.theme ?? 'day';
  const sky = THEME_SKY[theme];

  useEffect(() => {
    const queue: PageAudio[] = [];
    for (let p = level.startPage; p <= level.endPage; p++) {
      queue.push({
        page: p,
        file: `quran/audio/pages/${String(p).padStart(3, '0')}.mp3`,
      });
    }
    quranAudio.load(queue);
    void quranAudio.start();

    const onPage = (e: Event) =>
      setCurrentPage((e as CustomEvent<PageAudio>).detail);
    const onPlay = () => setPaused(false);
    const onPause = () => setPaused(true);

    quranAudio.addEventListener('page', onPage);
    quranAudio.addEventListener('play', onPlay);
    quranAudio.addEventListener('pause', onPause);
    return () => {
      quranAudio.removeEventListener('page', onPage);
      quranAudio.removeEventListener('play', onPlay);
      quranAudio.removeEventListener('pause', onPause);
      quranAudio.pause();
    };
  }, [level]);

  useEffect(() => {
    setResult(null);
    setStars(0);
    setCoins({ got: 0, total: 0 });
  }, [level.id]);

  useEffect(() => {
    const onWin = (r: LevelResult) => {
      const s = computeStars(r.coinsCollected, r.coinsTotal, r.timeMs);
      progress.record(r.levelId, s, r.timeMs, r.coinsCollected);
      setStars(s);
      setResult(r);
      quranAudio.pause();
    };
    const onCoins = (...args: unknown[]) => {
      const first = args[0];
      if (first && typeof first === 'object' && 'got' in (first as object)) {
        const p = first as CoinPayload;
        setCoins({ got: p.got, total: p.total });
      } else if (typeof first === 'number') {
        setCoins({ got: first, total: (args[1] as number) ?? 0 });
      }
    };
    bus.on('level:win', onWin);
    bus.on('coins:update', onCoins);
    return () => {
      bus.off('level:win', onWin);
      bus.off('coins:update', onCoins);
    };
  }, []);

  const toggleAudio = () => {
    if (paused) void quranAudio.resume();
    else quranAudio.pause();
  };

  return (
    <div
      style={{
        ...screen,
        background: `linear-gradient(180deg, ${sky.top} 0%, ${sky.bottom} 100%)`,
      }}
    >
      <div style={canvasWrap}>
        <PhaserGame level={level} />
        <TouchControls />

        {currentPage && (
          <div style={{ ...pill, top: 12, left: 12 }}>
            📖 <span className="ar" style={{ fontWeight: 800 }}>{currentPage.page}</span>
          </div>
        )}

        <div style={{ ...pill, top: 12, left: '50%', transform: 'translateX(-50%)' }}>
          🪙 <span style={{ fontWeight: 800 }}>{coins.got}/{coins.total}</span>
        </div>

        <div style={{
          ...pill,
          top: 12,
          right: 12,
          maxWidth: '46vw',
          direction: 'rtl',
          fontSize: 14,
          lineHeight: 1.25,
        }}>
          <span className="ar" style={{
            fontWeight: 800,
            whiteSpace: 'normal',
            textAlign: 'right',
          }}>
            {level.name}
          </span>
        </div>

        <button
          onClick={toggleAudio}
          style={{ ...circleBtn, position: 'absolute', bottom: 14, left: 14 }}
          title="Pause / resume audio"
        >
          {paused ? '▶' : '⏸'}
        </button>

        <button
          onClick={onExit}
          style={{ ...circleBtn, position: 'absolute', bottom: 14, right: 14 }}
          title="Exit"
        >✕</button>

        {result && (
          <div style={overlay}>
            <div style={celebration}>
              <div style={trophy}>🏆</div>
              <h2 style={winTitle}>Level Complete!</h2>
              <div style={{ fontSize: 56, marginTop: 4, letterSpacing: 8 }}>
                {[0, 1, 2].map(i => (
                  <span key={i} style={{
                    opacity: i < stars ? 1 : 0.18,
                    filter: i < stars ? 'drop-shadow(0 4px 6px rgba(255,200,0,0.7))' : 'none',
                    display: 'inline-block',
                  }}>⭐</span>
                ))}
              </div>
              <p className="ar" style={winSub}>أحسنت!</p>
              <p style={winTime}>
                ⏱ {(result.timeMs / 1000).toFixed(1)}s · 🪙 {result.coinsCollected} / {result.coinsTotal}
              </p>
              <div style={btnRow}>
                {hasNext && (
                  <button onClick={() => { setResult(null); onNext(); }}
                    style={{ ...bigBtn, background: 'linear-gradient(180deg, #69db7c, #37b24d)', boxShadow: '0 6px 0 #2b8a3e' }}>
                    ▶ Next
                  </button>
                )}
                <button onClick={() => { setResult(null); void quranAudio.resume(); }}
                  style={{ ...bigBtn, background: 'linear-gradient(180deg, #4dabf7, #1c7ed6)', boxShadow: '0 6px 0 #1864ab' }}>
                  🔁 Replay
                </button>
                <button onClick={onExit}
                  style={{ ...bigBtn, background: 'linear-gradient(180deg, #ffa94d, #e8590c)', boxShadow: '0 6px 0 #c4451a' }}>
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

const screen: CSSProperties = {
  display: 'grid', gridTemplateRows: '1fr', height: '100vh', width: '100%',
};
const canvasWrap: CSSProperties = {
  position: 'relative', overflow: 'hidden', width: '100%', height: '100%',
};
const pill: CSSProperties = {
  position: 'absolute', padding: '8px 14px', borderRadius: 999,
  background: 'rgba(255,255,255,0.92)', color: '#1a3a6a',
  fontSize: 14, fontWeight: 700,
  boxShadow: '0 3px 10px rgba(0,0,0,0.15)',
  backdropFilter: 'blur(6px)',
  display: 'flex', alignItems: 'center', gap: 6,
  pointerEvents: 'none',
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
  boxShadow: '0 20px 60px rgba(0,0,0,0.4)',
  maxWidth: '90vw',
};
const trophy: CSSProperties = { fontSize: 80, lineHeight: 1, marginBottom: 6 };
const winTitle: CSSProperties = {
  fontSize: 36, fontWeight: 900, margin: '8px 0 4px',
  color: '#1a3a6a',
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
