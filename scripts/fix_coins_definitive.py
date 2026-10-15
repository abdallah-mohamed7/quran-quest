"""Definitive coin HUD fix. Overwrites GameScreen + patches LevelScene emit."""
import pathlib, shutil, sys

ROOT = pathlib.Path(".").resolve()
if not (ROOT / "package.json").exists():
    print("❌ Run from inside quran-quest")
    sys.exit(1)

# ── 1. Replace GameScreen.tsx ────────────────────────────
GS = pathlib.Path("src/platform/GameScreen.tsx")
if GS.exists():
    shutil.copy2(GS, GS.with_suffix(".tsx.bak2"))
    print(f"  💾 {GS.with_suffix('.tsx.bak2')}")

GAME_SCREEN = r'''// src/platform/GameScreen.tsx
import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import PhaserGame from '../game/PhaserGame';
import { bus } from '../game/bus';
import { quranAudio } from '../game/systems/QuranAudio';
import { TouchControls } from './TouchControls';
import { progress, computeStars } from '../game/progress';
import type { LevelDef, LevelResult, PageAudio } from '../game/types';

type CoinPayload = { got: number; total: number };

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

    // Defensive: accept object OR two numbers OR undefined
    const onCoins = (...args: unknown[]) => {
      console.log('[coins:update] payload =', args);
      const first = args[0];
      if (first && typeof first === 'object' && 'got' in (first as object)) {
        const p = first as CoinPayload;
        setCoins({ got: p.got, total: p.total });
      } else if (typeof first === 'number') {
        setCoins({ got: first, total: (args[1] as number) ?? 0 });
      } else {
        console.warn('[coins:update] unrecognised payload:', args);
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
    <div style={screen}>
      <div style={canvasWrap}>
        <PhaserGame level={level} />
        <TouchControls />

        {currentPage && (
          <div style={{ ...pill, top: 14, left: 14 }}>
            📖 <span className="ar" style={{ fontWeight: 800 }}>صفحة {currentPage.page}</span>
          </div>
        )}

        <div style={{ ...pill, top: 14, left: '50%', transform: 'translateX(-50%)' }}>
          🪙 <span style={{ fontWeight: 800 }}>{coins.got} / {coins.total}</span>
        </div>

        <div style={{ ...pill, top: 14, right: 14 }}>
          <span className="ar" style={{ fontWeight: 800 }}>{level.name}</span>
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
              <p className="ar" style={winSub}>أحسنت! {level.name}</p>
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
  background: '#88ccff',
};
const canvasWrap: CSSProperties = {
  position: 'relative', overflow: 'hidden', width: '100%', height: '100%',
};
const pill: CSSProperties = {
  position: 'absolute', padding: '10px 18px', borderRadius: 999,
  background: 'rgba(255,255,255,0.92)', color: '#1a3a6a',
  fontSize: 16, fontWeight: 700,
  boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
  backdropFilter: 'blur(6px)',
  display: 'flex', alignItems: 'center', gap: 6,
  pointerEvents: 'none',
};
const circleBtn: CSSProperties = {
  width: 52, height: 52, borderRadius: '50%',
  background: 'rgba(255,255,255,0.92)', color: '#1a3a6a',
  fontSize: 22, fontWeight: 800,
  boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
  display: 'grid', placeItems: 'center',
  zIndex: 40,
};
const overlay: CSSProperties = {
  position: 'absolute', inset: 0, display: 'grid', placeItems: 'center',
  background: 'rgba(20,40,80,0.55)', backdropFilter: 'blur(8px)', zIndex: 100,
};
const celebration: CSSProperties = {
  position: 'relative', textAlign: 'center',
  padding: '40px 48px 32px',
  background: 'linear-gradient(180deg, #ffffff 0%, #f0f8ff 100%)',
  borderRadius: 32, border: '6px solid #ffd166',
  boxShadow: '0 20px 60px rgba(0,0,0,0.4)',
  maxWidth: '90vw',
};
const trophy: CSSProperties = { fontSize: 84, lineHeight: 1, marginBottom: 6 };
const winTitle: CSSProperties = {
  fontSize: 40, fontWeight: 900, margin: '8px 0 4px',
  color: '#1a3a6a', letterSpacing: -0.5,
};
const winSub: CSSProperties = {
  fontSize: 22, color: '#4a6a9a', fontWeight: 700, margin: '4px 0 12px',
};
const winTime: CSSProperties = {
  fontSize: 18, color: '#8a6a3a', fontWeight: 700, marginBottom: 24,
};
const btnRow: CSSProperties = {
  display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap',
};
const bigBtn: CSSProperties = {
  padding: '16px 28px', fontSize: 20, fontWeight: 800,
  color: '#fff', border: 'none', borderRadius: 20,
  cursor: 'pointer', fontFamily: 'inherit',
};
'''
GS.write_text(GAME_SCREEN, encoding="utf-8")
print(f"  ✅ rewrote {GS}")


# ── 2. Ensure LevelScene emits the object payload ────────
LS = pathlib.Path("src/game/scenes/LevelScene.ts")
if LS.exists():
    c = LS.read_text(encoding="utf-8")
    changed = False

    # Initial reset emit
    old1 = "    bus.emit('coins:update', { got: 0, total: this.coinsTotal });"
    new1 = "    bus.emit('coins:update', { got: 0, total: this.coinsTotal });"
    if old1 not in c and "coins:update" not in c:
        # no emit at all, insert after coins group
        anchor = "    this.coins = this.physics.add.staticGroup();"
        if anchor in c:
            c = c.replace(
                anchor,
                anchor + "\n    bus.emit('coins:update', { got: 0, total: (level.coins ?? []).length });",
                1,
            )
            changed = True

    # Collect coin emit
    if "this.coinsCollected++" in c and "coins:update" not in c:
        anchor = "this.coinsCollected++;"
        c = c.replace(
            anchor,
            anchor + "\n    bus.emit('coins:update', { got: this.coinsCollected, total: this.coinsTotal });",
            1,
        )
        changed = True

    if changed:
        shutil.copy2(LS, LS.with_suffix(".ts.bak3"))
        LS.write_text(c, encoding="utf-8")
        print(f"  ✅ patched {LS}")
    else:
        print(f"  ⏭  {LS} already has coins:update emits")


print("\n✅ Done. Now:")
print("  1. Stop dev server (Ctrl+C)")
print("  2. npm run dev -- --host")
print("  3. Hard-reload browser (Ctrl+Shift+R)")
print("  4. Open level 1, watch console for [coins:update] payload = ...")