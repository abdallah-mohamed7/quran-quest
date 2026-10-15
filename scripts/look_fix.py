"""Thin minimal look + fill screen. Redraws BootScene textures, updates PhaserGame scale."""
import pathlib, shutil, sys

ROOT = pathlib.Path(".").resolve()
if not (ROOT / "package.json").exists():
    print("❌ run from inside quran-quest")
    sys.exit(1)

# ── 1. BootScene — thin minimal textures ─────────────────
BS = ROOT / "src/game/scenes/BootScene.ts"
shutil.copy2(BS, BS.with_suffix(".ts.bak_thin"))

BOOT = r'''// src/game/scenes/BootScene.ts
import Phaser from 'phaser';
import { bus } from '../bus';

export class BootScene extends Phaser.Scene {
  constructor() { super('Boot'); }

  create() {
    this.makeBall();
    this.makePlatform();
    this.makeCoin();
    this.makeHazard();
    this.makeGoal();
    this.makeParticle();
    bus.emit('scene:ready');
    this.scene.start('Level');
  }

  // Solid ball, no outline, single subtle highlight. Rendered at 96px
  // so it stays crisp when scaled.
  private makeBall() {
    const S = 96, c = S / 2, r = 40;
    const g = this.add.graphics();
    g.fillStyle(0xff4a3a, 1).fillCircle(c, c, r);
    g.fillStyle(0xff7060, 1).fillCircle(c - r * 0.18, c - r * 0.18, r * 0.72);
    g.fillStyle(0xffa090, 1).fillCircle(c - r * 0.3, c - r * 0.3, r * 0.4);
    g.fillStyle(0xffffff, 0.85).fillCircle(c - r * 0.35, c - r * 0.35, r * 0.18);
    g.generateTexture('ball', S, S);
    g.destroy();
  }

  // Thin platform: 8px fill with 1px top accent. Pure white so tint works.
  private makePlatform() {
    const W = 64, H = 12;
    const g = this.add.graphics();
    // main bar — white so tint applies cleanly
    g.fillStyle(0xffffff, 1).fillRoundedRect(0, 2, W, 8, 4);
    // top accent line (subtle)
    g.fillStyle(0xdddddd, 1).fillRoundedRect(0, 2, W, 3, { tl: 4, tr: 4, bl: 0, br: 0 });
    g.generateTexture('platform', W, H);
    g.destroy();
  }

  // Thin ring coin. Empty inside so it looks delicate.
  private makeCoin() {
    const S = 48, c = S / 2;
    const g = this.add.graphics();
    g.fillStyle(0xffc933, 1).fillCircle(c, c, 14);        // filled
    g.fillStyle(0xfff0a0, 1).fillCircle(c, c, 10);        // inner lighter
    g.fillStyle(0xfffbe0, 1).fillCircle(c - 3, c - 3, 5); // highlight
    g.generateTexture('coin', S, S);
    g.destroy();
  }

  // Thin sharp triangles
  private makeHazard() {
    const W = 48, H = 24;
    const g = this.add.graphics();
    g.fillStyle(0xff3b3b, 1);
    for (let x = 0; x < W; x += 16) {
      g.fillTriangle(x, H, x + 8, 2, x + 16, H);
    }
    g.generateTexture('hazard', W, H);
    g.destroy();
  }

  // Portal: concentric thin rings, no thick fills
  private makeGoal() {
    const W = 100, H = 140, cx = W / 2, cy = H / 2;
    const g = this.add.graphics();
    g.fillStyle(0xffffff, 0.15).fillCircle(cx, cy, 46);
    g.lineStyle(4, 0xffffff, 0.9).strokeCircle(cx, cy, 44);
    g.lineStyle(3, 0x88ddff, 1).strokeCircle(cx, cy, 34);
    g.lineStyle(2, 0xffd166, 1).strokeCircle(cx, cy, 24);
    g.fillStyle(0xffffff, 1).fillCircle(cx, cy, 8);
    g.generateTexture('goal', W, H);
    g.destroy();
  }

  private makeParticle() {
    const S = 10, c = S / 2;
    const g = this.add.graphics();
    g.fillStyle(0xffffff, 1).fillCircle(c, c, c);
    g.generateTexture('particle', S, S);
    g.destroy();
  }
}
'''
BS.write_text(BOOT, encoding="utf-8")
print(f"  ✅ BootScene.ts — thin minimal textures")


# ── 2. PhaserGame — fill screen exactly ──────────────────
PG = ROOT / "src/game/PhaserGame.tsx"
shutil.copy2(PG, PG.with_suffix(".tsx.bak_thin"))

PHASER_GAME = r'''// src/game/PhaserGame.tsx
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
'''
PG.write_text(PHASER_GAME, encoding="utf-8")
print(f"  ✅ PhaserGame.tsx — Scale.RESIZE, no letterbox")


# ── 3. LevelScene — camera no longer needs 1.333 zoom, use viewport ─
LS = ROOT / "src/game/scenes/LevelScene.ts"
shutil.copy2(LS, LS.with_suffix(".ts.bak_thin"))

c = LS.read_text(encoding="utf-8")
# Remove the old zoom line
c = c.replace(
    "    this.cameras.main.setZoom(1280 / 960);",
    "    this.cameras.main.setZoom(1);",
)
# Bump platform body height (textures are now 12px tall, need to scale properly)
c = c.replace(
    "      s.setDisplaySize(p.w, p.h).refreshBody();",
    "      s.setDisplaySize(p.w, Math.max(p.h, 16)).refreshBody();",
)
LS.write_text(c, encoding="utf-8")
print(f"  ✅ LevelScene.ts — no zoom, adaptive platform height")


print("\n✅ Done. Now:")
print("  1. Stop dev server (Ctrl+C)")
print("  2. npm run dev -- --host")
print("  3. Reload the browser")
print("\nNote: The letterbox bars are gone.")
print("The ball is smooth (96px texture).")
print("Platforms are thin 8px slivers instead of chunky blocks.")