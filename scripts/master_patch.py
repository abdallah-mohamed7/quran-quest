"""
quran-quest · master auto-patch.
Adds: touch controls, HD resolution, stars, save progress, coin HUD.
Excludes: audio/music changes.

Run from inside C:\\Users\\amaha\\quran-quest:
    python scripts/master_patch.py
Every modified file gets a *.bak backup (only the first time).
"""

import pathlib
import shutil
import sys

ROOT = pathlib.Path(".").resolve()
print(f"📁 Working in: {ROOT}\n")

if not (ROOT / "package.json").exists():
    print("❌ Not in quran-quest folder. cd into it first.")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════
def backup(p: pathlib.Path):
    bak = p.with_suffix(p.suffix + ".bak")
    if not bak.exists() and p.exists():
        shutil.copy2(p, bak)
        print(f"  💾 backup: {bak}")

def write(p_str: str, content: str) -> bool:
    p = pathlib.Path(p_str)
    if p.exists():
        print(f"  ⏭  exists: {p}")
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  ✅ wrote: {p}")
    return True

def patch(p_str: str, replacements: list, label: str = "") -> int:
    """Apply exact-string replacements. Skips if 'already present'."""
    p = pathlib.Path(p_str)
    if not p.exists():
        print(f"  ❌ missing: {p}")
        return 0
    src = p.read_text(encoding="utf-8")
    orig = src
    hits = 0
    for anchor, replacement, already in replacements:
        if already in src:
            print(f"  ⏭  already present: {already[:50]!r}")
            continue
        if anchor not in src:
            print(f"  ⚠  anchor not found: {anchor[:60]!r}")
            continue
        src = src.replace(anchor, replacement, 1)
        hits += 1
    if src != orig:
        backup(p)
        p.write_text(src, encoding="utf-8")
    print(f"  🔧 {p_str}: {hits} replacement(s)")
    return hits


# ═══════════════════════════════════════════════════════════════════
# SECTION 1 — New files
# ═══════════════════════════════════════════════════════════════════
print("\n═══ 1/7  Writing new files ═══")

PROGRESS_TS = '''// src/game/progress.ts
const KEY = 'quran-quest-progress';

export type LevelProgress = {
  stars: 0 | 1 | 2 | 3;
  bestTimeMs: number;
  coinsCollected: number;
  completed: boolean;
};

export type ProgressMap = Record<string, LevelProgress>;

function load(): ProgressMap {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) as ProgressMap : {};
  } catch {
    return {};
  }
}

function save(p: ProgressMap): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(p));
  } catch {}
}

export const progress = {
  getAll(): ProgressMap {
    return load();
  },

  get(levelId: string): LevelProgress | undefined {
    return load()[levelId];
  },

  record(
    levelId: string,
    stars: number,
    timeMs: number,
    coinsCollected: number,
  ): LevelProgress {
    const all = load();
    const prev = all[levelId];
    const clampedStars = Math.max(0, Math.min(3, stars)) as 0 | 1 | 2 | 3;
    const next: LevelProgress = {
      stars: prev ? (Math.max(prev.stars, clampedStars) as 0 | 1 | 2 | 3) : clampedStars,
      bestTimeMs: prev ? Math.min(prev.bestTimeMs, timeMs) : timeMs,
      coinsCollected: prev ? Math.max(prev.coinsCollected, coinsCollected) : coinsCollected,
      completed: true,
    };
    all[levelId] = next;
    save(all);
    return next;
  },

  clear(): void {
    localStorage.removeItem(KEY);
  },
};

export function computeStars(
  coinsCollected: number,
  coinsTotal: number,
  timeMs: number,
): number {
  let s = 1;
  if (coinsTotal > 0 && coinsCollected / coinsTotal >= 0.6) s++;
  if (timeMs < 60000) s++;
  return s;
}
'''

TOUCH_CONTROLS_TSX = '''// src/platform/TouchControls.tsx
import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import { bus } from '../game/bus';

export function TouchControls() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const isTouch =
      'ontouchstart' in window ||
      (navigator.maxTouchPoints ?? 0) > 0;
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
'''

write("src/game/progress.ts", PROGRESS_TS)
write("src/platform/TouchControls.tsx", TOUCH_CONTROLS_TSX)


# ═══════════════════════════════════════════════════════════════════
# SECTION 2 — Rewrite types.ts (add coinsCollected / coinsTotal)
# ═══════════════════════════════════════════════════════════════════
print("\n═══ 2/7  Updating types.ts ═══")

TYPES_TS = '''// src/game/types.ts

export type PageAudio = {
  page: number;
  file: string;
};

export type Rect = {
  x: number;
  y: number;
  w: number;
  h: number;
};

export type Theme = 'day' | 'sunset' | 'forest' | 'candy' | 'ocean';

export type LevelDef = {
  id: string;
  name: string;
  theme?: Theme;
  startPage: number;
  endPage: number;
  spawn: { x: number; y: number };
  platforms: Rect[];
  hazards: Rect[];
  coins: { x: number; y: number }[];
  goal: Rect;
};

export type LevelResult = {
  levelId: string;
  timeMs: number;
  coinsCollected: number;
  coinsTotal: number;
};
'''

patch("src/game/types.ts", [
    (
        # if user's file still has 2-field LevelResult, replace entire file
        "__REPLACE_WHOLE_FILE__",  # never matches, we do this differently below
        "",
        "__NEVER__",
    ),
])

# simpler: overwrite types.ts entirely if LevelResult lacks coinsCollected
types_path = pathlib.Path("src/game/types.ts")
if types_path.exists():
    content = types_path.read_text(encoding="utf-8")
    if "coinsCollected" not in content:
        backup(types_path)
        types_path.write_text(TYPES_TS, encoding="utf-8")
        print(f"  ✅ rewrote: {types_path}")
    else:
        print(f"  ⏭  already has coinsCollected")


# ═══════════════════════════════════════════════════════════════════
# SECTION 3 — HD resolution in PhaserGame.tsx
# ═══════════════════════════════════════════════════════════════════
print("\n═══ 3/7  HD resolution ═══")

PHASER_GAME_TSX = '''// src/game/PhaserGame.tsx
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

    gameRef.current = new Phaser.Game({
      type: Phaser.AUTO,
      parent: hostRef.current,
      width: 1280,
      height: 720,
      backgroundColor: '#88ccff',
      antialias: true,
      roundPixels: false,
      pixelArt: false,
      physics: {
        default: 'arcade',
        arcade: { gravity: { x: 0, y: 1000 }, debug: false },
      },
      scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH,
      },
      scene: [BootScene, LevelScene],
    });

    return () => {
      gameRef.current?.destroy(true);
      gameRef.current = null;
    };
  }, []);

  useEffect(() => {
    state.currentLevel = level;
    console.log('[PhaserGame] set currentLevel:', level.id);
    const t = window.setTimeout(() => {
      bus.emit('level:load', level);
    }, 0);
    return () => window.clearTimeout(t);
  }, [level]);

  return (
    <div
      ref={hostRef}
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    />
  );
}
'''

pg_path = pathlib.Path("src/game/PhaserGame.tsx")
if pg_path.exists():
    c = pg_path.read_text(encoding="utf-8")
    if "width: 1280" not in c:
        backup(pg_path)
        pg_path.write_text(PHASER_GAME_TSX, encoding="utf-8")
        print(f"  ✅ rewrote for 1280x720")
    else:
        print(f"  ⏭  already 1280x720")


# ═══════════════════════════════════════════════════════════════════
# SECTION 4 — Patch LevelScene.ts
# ═══════════════════════════════════════════════════════════════════
print("\n═══ 4/7  Patching LevelScene.ts ═══")

LS = "src/game/scenes/LevelScene.ts"

patch(LS, [
    # 4a — add coin tracking fields next to landedThisFrame
    (
        "  private landedThisFrame = false;",
        "  private landedThisFrame = false;\n"
        "  private coinsCollected = 0;\n"
        "  private coinsTotal = 0;",
        "private coinsCollected = 0;",
    ),

    # 4b — init coin counters in loadLevel
    (
        "    this.coins = this.physics.add.staticGroup();",
        "    this.coinsCollected = 0;\n"
        "    this.coinsTotal = (level.coins ?? []).length;\n\n"
        "    this.coins = this.physics.add.staticGroup();",
        "this.coinsTotal = (level.coins ?? []).length",
    ),

    # 4c — increment on collect
    (
        "  private collectCoin(coin: Phaser.Physics.Arcade.Sprite): void {\n"
        "    this.burstParticles(coin.x, coin.y, 0xffd166, 10);\n"
        "    coin.destroy();\n"
        "  }",
        "  private collectCoin(coin: Phaser.Physics.Arcade.Sprite): void {\n"
        "    this.burstParticles(coin.x, coin.y, 0xffd166, 10);\n"
        "    coin.destroy();\n"
        "    this.coinsCollected++;\n"
        "  }",
        "this.coinsCollected++",
    ),

    # 4d — emit coins in win()
    (
        "    bus.emit('level:win', {\n"
        "      levelId: this.level.id,\n"
        "      timeMs: Math.round(this.time.now - this.startTime),\n"
        "    });",
        "    bus.emit('level:win', {\n"
        "      levelId: this.level.id,\n"
        "      timeMs: Math.round(this.time.now - this.startTime),\n"
        "      coinsCollected: this.coinsCollected,\n"
        "      coinsTotal: this.coinsTotal,\n"
        "    });",
        "coinsCollected: this.coinsCollected,",
    ),

    # 4e — camera zoom for HD rendering
    (
        "    this.cameras.main.startFollow(this.player, true, 0.14, 0.14, -200, 40);",
        "    this.cameras.main.startFollow(this.player, true, 0.14, 0.14, -200, 40);\n"
        "    this.cameras.main.setZoom(1280 / 960);",
        "setZoom(1280 / 960)",
    ),
])


# ═══════════════════════════════════════════════════════════════════
# SECTION 5 — Rewrite GameScreen.tsx
# ═══════════════════════════════════════════════════════════════════
print("\n═══ 5/7  Rewriting GameScreen.tsx ═══")

GAME_SCREEN_TSX = '''// src/platform/GameScreen.tsx
import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import PhaserGame from '../game/PhaserGame';
import { bus } from '../game/bus';
import { quranAudio } from '../game/systems/QuranAudio';
import { TouchControls } from './TouchControls';
import { progress, computeStars } from '../game/progress';
import type { LevelDef, LevelResult, PageAudio } from '../game/types';

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
  const [coinHud, setCoinHud] = useState({ got: 0, total: 0 });

  // Load + play audio for this level
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

  // Reset win state when level changes
  useEffect(() => {
    setResult(null);
    setStars(0);
  }, [level.id]);

  // Win handler
  useEffect(() => {
    const onWin = (r: LevelResult) => {
      const s = computeStars(r.coinsCollected, r.coinsTotal, r.timeMs);
      progress.record(r.levelId, s, r.timeMs, r.coinsCollected);
      setStars(s);
      setResult(r);
      quranAudio.pause();
    };
    const onCoin = (e: Event) => {
      const d = (e as CustomEvent<{ got: number; total: number }>).detail;
      setCoinHud(d);
    };
    bus.on('level:win', onWin);
    bus.on('coins:update', onCoin);
    return () => {
      bus.off('level:win', onWin);
      bus.off('coins:update', onCoin);
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
            <span style={{ fontSize: 20, marginRight: 6 }}>📖</span>
            <span className="ar" style={{ fontWeight: 800 }}>
              صفحة {currentPage.page}
            </span>
          </div>
        )}

        <div style={{ ...pill, top: 14, left: '50%', transform: 'translateX(-50%)' }}>
          <span style={{ marginRight: 6 }}>🪙</span>
          <span style={{ fontWeight: 800 }}>
            {coinHud.got} / {coinHud.total}
          </span>
        </div>

        <div style={{ ...pill, top: 14, right: 14 }}>
          <span className="ar" style={{ fontWeight: 800 }}>{level.name}</span>
        </div>

        <div style={bottomLeft}>
          <button onClick={toggleAudio} style={circleBtn} title="Pause / resume audio">
            {paused ? '▶' : '⏸'}
          </button>
          <button onClick={() => quranAudio.setVolume(0.15)} style={circleBtn} title="Quiet">🔉</button>
          <button onClick={() => quranAudio.setVolume(0.9)} style={circleBtn} title="Loud">🔊</button>
        </div>

        <button
          onClick={onExit}
          style={{ ...circleBtn, position: 'absolute', bottom: 14, right: 14, width: 56, height: 56, fontSize: 24 }}
          title="Exit"
        >
          ✕
        </button>

        {result && (
          <div style={overlay}>
            <div style={celebration}>
              {[...Array(20)].map((_, i) => (
                <div key={i} style={{
                  position: 'absolute', top: -20, left: `${(i * 5) % 100}%`,
                  fontSize: 24 + (i % 3) * 8,
                  animation: `float ${2 + (i % 3)}s ease-in-out ${i * 0.1}s infinite`,
                  opacity: 0.9,
                }}>
                  {['⭐', '🎉', '✨', '🏆', '🌟'][i % 5]}
                </div>
              ))}
              <div style={trophy}>🏆</div>
              <h2 style={winTitle}>Level Complete!</h2>

              <div style={{ fontSize: 56, marginTop: 4, letterSpacing: 8 }}>
                {[0, 1, 2].map(i => (
                  <span key={i} style={{
                    opacity: i < stars ? 1 : 0.18,
                    filter: i < stars ? 'drop-shadow(0 4px 6px rgba(255,200,0,0.7))' : 'none',
                    display: 'inline-block',
                    animation: i < stars ? `twinkle ${1.4 + i * 0.3}s ease-in-out infinite` : 'none',
                  }}>⭐</span>
                ))}
              </div>

              <p className="ar" style={winSub}>أحسنت! {level.name}</p>
              <p style={winTime}>
                ⏱ {(result.timeMs / 1000).toFixed(1)}s &nbsp;·&nbsp; 🪙 {result.coinsCollected} / {result.coinsTotal}
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
  display: 'flex', alignItems: 'center', pointerEvents: 'none',
};
const bottomLeft: CSSProperties = {
  position: 'absolute', bottom: 14, left: 14,
  display: 'flex', gap: 10,
};
const circleBtn: CSSProperties = {
  width: 52, height: 52, borderRadius: '50%',
  background: 'rgba(255,255,255,0.92)', color: '#1a3a6a',
  fontSize: 22, fontWeight: 800,
  boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
  display: 'grid', placeItems: 'center',
  transition: 'transform 0.08s ease',
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
  boxShadow: '0 20px 60px rgba(0,0,0,0.4), 0 0 0 6px rgba(255,255,255,0.4)',
  maxWidth: '90vw', overflow: 'hidden',
  animation: 'pulse 1.2s ease-in-out 1',
};
const trophy: CSSProperties = {
  fontSize: 84, lineHeight: 1, marginBottom: 6,
  filter: 'drop-shadow(0 6px 0 rgba(0,0,0,0.15)) drop-shadow(0 12px 24px rgba(255,209,102,0.6))',
};
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
  cursor: 'pointer', letterSpacing: 0.5,
  fontFamily: 'inherit', transition: 'transform 0.08s ease',
};
'''

gs_path = pathlib.Path("src/platform/GameScreen.tsx")
if gs_path.exists():
    backup(gs_path)
gs_path.write_text(GAME_SCREEN_TSX, encoding="utf-8")
print(f"  ✅ rewrote: {gs_path}")


# ═══════════════════════════════════════════════════════════════════
# SECTION 6 — Rewrite LevelSelect.tsx (stars on cards + best time)
# ═══════════════════════════════════════════════════════════════════
print("\n═══ 6/7  Rewriting LevelSelect.tsx ═══")

LEVEL_SELECT_TSX = '''// src/platform/LevelSelect.tsx
import type { CSSProperties } from 'react';
import levels from '../game/levels';
import { progress } from '../game/progress';

const CARD_COLORS = [
  '#ff6b6b', '#ffa94d', '#ffd43b', '#69db7c', '#38d9a9',
  '#4dabf7', '#748ffc', '#da77f2', '#f783ac', '#ff8c42',
];

const CARD_ICONS = ['🌱', '🌊', '⛰️', '🌳', '🌈', '🍭', '⭐', '🎯', '🔥', '🏆'];

function shade(hex: string): string {
  const n = parseInt(hex.slice(1), 16);
  const r = Math.max(0, ((n >> 16) & 0xff) - 60);
  const g = Math.max(0, ((n >> 8) & 0xff) - 60);
  const b = Math.max(0, (n & 0xff) - 60);
  return `rgb(${r},${g},${b})`;
}

export default function LevelSelect({
  onPick,
  onBack,
}: {
  onPick: (levelId: string) => void;
  onBack: () => void;
}) {
  return (
    <div style={wrap}>
      <div style={header}>
        <h1 style={title}><span className="ar">اختر مرحلة</span></h1>
        <p style={sub}>Choose your adventure</p>
      </div>

      <div style={grid}>
        {levels.map((lvl, i) => {
          const p = progress.get(lvl.id);
          const stars = p?.stars ?? 0;
          const best = p?.bestTimeMs;
          return (
            <button
              key={lvl.id}
              onClick={() => onPick(lvl.id)}
              style={{
                ...card,
                background: `linear-gradient(180deg, ${CARD_COLORS[i % 10]} 0%, ${CARD_COLORS[i % 10]}cc 100%)`,
                boxShadow: `0 6px 0 ${shade(CARD_COLORS[i % 10])}, 0 12px 24px rgba(0,0,0,0.15)`,
              }}
              onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-6px) rotate(-1deg)')}
              onMouseLeave={(e) => (e.currentTarget.style.transform = '')}
            >
              <div style={icon}>{CARD_ICONS[i % 10]}</div>
              <div style={number}>{i + 1}</div>
              <div className="ar" style={name}>{lvl.name}</div>

              <div style={{ fontSize: 18, marginTop: 6, letterSpacing: 2 }}>
                {[0, 1, 2].map(s => (
                  <span key={s} style={{ opacity: s < stars ? 1 : 0.22 }}>⭐</span>
                ))}
              </div>

              {best !== undefined && (
                <div style={{ fontSize: 11, marginTop: 4, opacity: 0.9, fontWeight: 700 }}>
                  ⏱ {(best / 1000).toFixed(1)}s
                </div>
              )}
            </button>
          );
        })}
      </div>

      <button onClick={onBack} style={backBtn}>
        ← <span className="ar">رجوع</span>
      </button>

      <div style={grass} />
    </div>
  );
}

const wrap: CSSProperties = {
  minHeight: '100vh', padding: '32px 24px 80px',
  display: 'flex', flexDirection: 'column', alignItems: 'center',
  background: 'linear-gradient(180deg, #7ecbff 0%, #bfe5ff 60%, #d8f5c0 100%)',
  overflowY: 'auto', position: 'relative',
};
const header: CSSProperties = { textAlign: 'center', marginBottom: 32 };
const title: CSSProperties = {
  fontSize: 'clamp(36px, 6vw, 56px)', margin: 0,
  color: '#1a3a6a', fontWeight: 900,
  textShadow: '0 3px 0 rgba(255,255,255,0.8)',
};
const sub: CSSProperties = {
  fontSize: 18, color: '#4a6a9a', margin: '6px 0 0', fontWeight: 600,
};
const grid: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
  gap: 20, maxWidth: 820, width: '100%', zIndex: 2,
};
const card: CSSProperties = {
  position: 'relative', display: 'flex', flexDirection: 'column',
  alignItems: 'center', padding: '18px 14px 16px',
  borderRadius: 24, color: '#fff',
  border: '4px solid rgba(255,255,255,0.85)',
  cursor: 'pointer',
  transition: 'transform 0.18s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.18s ease',
  fontFamily: 'inherit', minHeight: 180,
};
const icon: CSSProperties = {
  fontSize: 44, lineHeight: 1, marginBottom: 6,
  filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))',
};
const number: CSSProperties = {
  position: 'absolute', top: -14, left: -14,
  width: 42, height: 42, lineHeight: '42px',
  borderRadius: '50%', background: '#fff',
  color: '#1a3a6a', fontWeight: 900, fontSize: 20,
  textAlign: 'center', border: '3px solid rgba(0,0,0,0.15)',
  boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
};
const name: CSSProperties = {
  fontSize: 14, fontWeight: 800, textAlign: 'center',
  lineHeight: 1.25, color: '#fff',
  textShadow: '0 2px 4px rgba(0,0,0,0.3)', marginTop: 4,
};
const backBtn: CSSProperties = {
  marginTop: 40, padding: '14px 32px',
  fontSize: 20, fontWeight: 800, color: '#1a3a6a',
  background: '#fff', borderRadius: 999,
  boxShadow: '0 6px 0 #b8d0e0, 0 12px 24px rgba(0,0,0,0.15)',
  transition: 'transform 0.08s ease', zIndex: 2,
};
const grass: CSSProperties = {
  position: 'fixed', bottom: 0, left: 0, right: 0, height: 40,
  background: 'linear-gradient(180deg, #6cc24a 0%, #4a9c30 100%)',
  borderRadius: '60% 60% 0 0 / 40px 40px 0 0',
  pointerEvents: 'none',
};
'''

ls_path = pathlib.Path("src/platform/LevelSelect.tsx")
if ls_path.exists():
    backup(ls_path)
ls_path.write_text(LEVEL_SELECT_TSX, encoding="utf-8")
print(f"  ✅ rewrote: {ls_path}")


# ═══════════════════════════════════════════════════════════════════
# SECTION 7 — Add reset progress button in Menu.tsx
# ═══════════════════════════════════════════════════════════════════
print("\n═══ 7/7  Adding reset button to Menu.tsx ═══")

patch("src/platform/Menu.tsx", [
    (
        "import type { CSSProperties } from 'react';",
        "import type { CSSProperties } from 'react';\n"
        "import { progress } from '../game/progress';",
        "import { progress } from '../game/progress';",
    ),
    (
        "        <p style={hint}>\n"
        "          ← → move &nbsp;·&nbsp; SPACE jump &nbsp;·&nbsp; R restart\n"
        "        </p>",
        "        <p style={hint}>\n"
        "          ← → move &nbsp;·&nbsp; SPACE jump &nbsp;·&nbsp; R restart\n"
        "        </p>\n\n"
        "        <button\n"
        "          onClick={() => {\n"
        "            if (window.confirm('Reset all stars and progress?')) {\n"
        "              progress.clear();\n"
        "              window.location.reload();\n"
        "            }\n"
        "          }}\n"
        "          style={resetBtn}\n"
        "        >\n"
        "          🔄 Reset progress\n"
        "        </button>",
        "Reset all stars and progress",
    ),
    (
        "const star: CSSProperties = {",
        "const resetBtn: CSSProperties = {\n"
        "  marginTop: 18,\n"
        "  padding: '8px 18px',\n"
        "  fontSize: 14,\n"
        "  fontWeight: 700,\n"
        "  color: '#3a5a8a',\n"
        "  background: 'rgba(255,255,255,0.7)',\n"
        "  borderRadius: 999,\n"
        "  border: '2px solid rgba(255,255,255,0.9)',\n"
        "  cursor: 'pointer',\n"
        "  fontFamily: 'inherit',\n"
        "  opacity: 0.85,\n"
        "};\n\n"
        "const star: CSSProperties = {",
        "resetBtn: CSSProperties",
    ),
])


# ═══════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("✅ Master patch complete.")
print("=" * 60)
print("""
Next:
  1. npx tsc --noEmit        # type check
  2. npm run dev             # start dev server
  3. Test on desktop + phone

Backups are in *.bak files. Delete them when happy:
  Get-ChildItem -Recurse -Filter *.bak | Remove-Item
""")