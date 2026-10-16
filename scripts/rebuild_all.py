"""
Full clean rebuild of quran-quest.
Backs up src/, deletes it, writes known-good versions of every file.
Run: python scripts/rebuild_all.py
"""
import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(".").resolve()
if not (ROOT / "package.json").exists():
    print("X  Run from inside quran-quest")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# 0. Backup + wipe src/
# ═══════════════════════════════════════════════════════════════
print("═══ 0/3  Backup + wipe src/ ═══")

SRC = ROOT / "src"
BACKUP = ROOT / "_backups" / f"src_before_rebuild"
if BACKUP.exists():
    shutil.rmtree(BACKUP)
if SRC.exists():
    shutil.move(str(SRC), str(BACKUP))
    print(f"  💾 old src → {BACKUP.relative_to(ROOT)}")

SRC.mkdir()
(SRC / "game").mkdir()
(SRC / "game" / "scenes").mkdir()
(SRC / "game" / "systems").mkdir()
(SRC / "game" / "levels").mkdir()
(SRC / "platform").mkdir()
print("  ✅ fresh src/ created")


# ═══════════════════════════════════════════════════════════════
# 1. Write every source file
# ═══════════════════════════════════════════════════════════════
print("\n═══ 1/3  Writing source files ═══")

FILES: dict[str, str] = {}

FILES["src/main.tsx"] = r"""import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
"""

FILES["src/index.css"] = r"""@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&family=Cairo:wght@500;700;900&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, #root {
  height: 100%;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Baloo 2', system-ui, sans-serif;
  background: #a8d8ff;
  color: #1a2a4a;
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
  -webkit-tap-highlight-color: transparent;
}

.ar { font-family: 'Cairo', system-ui, sans-serif; }

button {
  font-family: inherit;
  cursor: pointer;
  border: none;
  background: none;
  color: inherit;
  -webkit-tap-highlight-color: transparent;
}
button:active { transform: translateY(1px); }

canvas {
  display: block;
  outline: none;
  user-select: none;
  -webkit-user-select: none;
  touch-action: none;
}

@keyframes floaty { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-12px)} }
@keyframes bob { 0%,100%{transform:rotate(-3deg) translateY(0)} 50%{transform:rotate(3deg) translateY(-8px)} }
@keyframes twinkle { 0%,100%{opacity:0.35; transform:scale(0.9)} 50%{opacity:1; transform:scale(1.15)} }
@keyframes popIn { 0%{transform:scale(0.7); opacity:0} 100%{transform:scale(1); opacity:1} }
"""

FILES["src/game/types.ts"] = r"""export type Rect = { x: number; y: number; w: number; h: number };
export type Theme = 'day' | 'sunset' | 'forest' | 'candy' | 'ocean';

export type Decoration = { x: number; y: number; kind: 'tree' | 'bush' };

export type LevelDef = {
  id: string;
  name: string;
  theme: Theme;
  surah: number;
  spawn: { x: number; y: number };
  platforms: Rect[];
  hazards: Rect[];
  coins: { x: number; y: number }[];
  goal: Rect;
  decorations: Decoration[];
};

export type LevelResult = {
  levelId: string;
  timeMs: number;
  coinsCollected: number;
  coinsTotal: number;
};

export type Ayah = { surah: number; ayah: number; file: string };
"""

FILES["src/game/bus.ts"] = r"""import Phaser from 'phaser';
import type { LevelDef } from './types';

export const bus = new Phaser.Events.EventEmitter();
export const state = { currentLevel: null as LevelDef | null };
"""

FILES["src/game/progress.ts"] = r"""const KEY = 'quran-quest-progress';

export type LevelProgress = {
  stars: 0 | 1 | 2 | 3;
  bestTimeMs: number;
  coinsCollected: number;
  completed: boolean;
};
export type ProgressMap = Record<string, LevelProgress>;

function load(): ProgressMap {
  try {
    const r = localStorage.getItem(KEY);
    return r ? JSON.parse(r) : {};
  } catch { return {}; }
}
function save(p: ProgressMap) {
  try { localStorage.setItem(KEY, JSON.stringify(p)); } catch {}
}

export const progress = {
  getAll(): ProgressMap { return load(); },
  get(id: string): LevelProgress | undefined { return load()[id]; },
  record(id: string, stars: number, timeMs: number, coins: number): LevelProgress {
    const all = load();
    const prev = all[id];
    const s = Math.max(0, Math.min(3, stars)) as 0 | 1 | 2 | 3;
    const next: LevelProgress = {
      stars: prev ? (Math.max(prev.stars, s) as 0 | 1 | 2 | 3) : s,
      bestTimeMs: prev ? Math.min(prev.bestTimeMs, timeMs) : timeMs,
      coinsCollected: prev ? Math.max(prev.coinsCollected, coins) : coins,
      completed: true,
    };
    all[id] = next;
    save(all);
    return next;
  },
  clear(): void { localStorage.removeItem(KEY); },
};

export function computeStars(coins: number, total: number, timeMs: number): number {
  let s = 1;
  if (total > 0 && coins / total >= 0.6) s++;
  if (timeMs < 90000) s++;
  return s;
}
"""

FILES["src/game/systems/QuranAudio.ts"] = r"""import type { Ayah } from '../types';

export class QuranAudio extends EventTarget {
  private el = new Audio();
  private queue: Ayah[] = [];
  private index = 0;
  private started = false;

  constructor() {
    super();
    this.el.volume = 0.5;
    this.el.preload = 'auto';
    this.el.addEventListener('ended', () => this.next());
    this.el.addEventListener('play', () => this.dispatchEvent(new Event('play')));
    this.el.addEventListener('pause', () => this.dispatchEvent(new Event('pause')));
  }

  load(ayahs: Ayah[]): void {
    this.queue = ayahs;
    this.index = 0;
  }

  async start(): Promise<void> {
    if (!this.queue.length) return;
    this.started = true;
    await this.playCurrent();
  }

  async resume(): Promise<void> {
    if (!this.started) return this.start();
    try { await this.el.play(); } catch {}
  }

  pause(): void { try { this.el.pause(); } catch {} }

  setVolume(v: number): void {
    this.el.volume = Math.max(0, Math.min(1, v));
  }

  get current(): Ayah | undefined { return this.queue[this.index]; }

  private async playCurrent(): Promise<void> {
    const cur = this.current;
    if (!cur) return;
    this.el.src = cur.file.startsWith('/') ? cur.file.slice(1) : cur.file;
    try {
      await this.el.play();
    } catch {}
    this.dispatchEvent(new CustomEvent<Ayah>('ayah', { detail: cur }));
  }

  private next(): void {
    if (!this.queue.length) return;
    this.index = (this.index + 1) % this.queue.length;
    void this.playCurrent();
  }
}

export const quranAudio = new QuranAudio();
"""

FILES["src/game/PhaserGame.tsx"] = r"""import { useEffect, useRef } from 'react';
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

    gameRef.current = new Phaser.Game({
      type: Phaser.AUTO,
      parent,
      width: parent.clientWidth || window.innerWidth,
      height: parent.clientHeight || window.innerHeight,
      backgroundColor: '#c8e8ff',
      antialias: true,
      pixelArt: false,
      roundPixels: false,
      physics: { default: 'arcade', arcade: { gravity: { x: 0, y: 1100 }, debug: false } },
      scale: {
        mode: Phaser.Scale.RESIZE,
        autoCenter: Phaser.Scale.CENTER_BOTH,
        width: '100%',
        height: '100%',
      },
      scene: [BootScene, LevelScene],
    });

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

  return <div ref={hostRef} style={{ width: '100%', height: '100%', overflow: 'hidden' }} />;
}
"""

FILES["src/game/scenes/BootScene.ts"] = r"""import Phaser from 'phaser';
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
    this.makeTree();
    this.makeBush();
    bus.emit('scene:ready');
    this.scene.start('Level');
  }

  // Smooth red ball — 96px texture, no outline, soft gradient + tiny specular
  private makeBall() {
    const S = 96, c = S / 2, r = 40;
    const g = this.add.graphics();
    // Deep base
    g.fillStyle(0xd63535, 1).fillCircle(c, c, r);
    // Mid tones — concentric circles simulating a radial gradient
    g.fillStyle(0xe94a4a, 1).fillCircle(c - 1, c - 1, r - 2);
    g.fillStyle(0xf55f5f, 1).fillCircle(c - 3, c - 3, r - 8);
    g.fillStyle(0xfc7a7a, 1).fillCircle(c - 6, c - 6, r - 15);
    g.fillStyle(0xffa0a0, 1).fillCircle(c - 10, c - 10, r - 22);
    // Bright specular
    g.fillStyle(0xffffff, 0.9).fillCircle(c - r * 0.4, c - r * 0.45, r * 0.14);
    g.generateTexture('ball', S, S);
    g.destroy();
  }

  // Thin platform — 96x20 with soft grass tufts, pure white for tinting
  private makePlatform() {
    const W = 96, H = 20;
    const g = this.add.graphics();
    // Main body
    g.fillStyle(0xffffff, 1).fillRoundedRect(0, 6, W, H - 6, 4);
    // Top edge shading
    g.fillStyle(0xeaeaea, 1).fillRoundedRect(0, 6, W, 4, { tl: 4, tr: 4, bl: 0, br: 0 });
    // Grass tufts — small triangles of varying height
    g.fillStyle(0xffffff, 1);
    for (let x = 2; x < W - 4; x += 9) {
      const peak = 4 + ((x / 3) % 4);
      g.fillTriangle(x, 6, x + 4, 6 - peak, x + 8, 6);
    }
    g.generateTexture('platform', W, H);
    g.destroy();
  }

  // Coin — gold with soft ring + shine
  private makeCoin() {
    const S = 44, c = S / 2;
    const g = this.add.graphics();
    // Shadow ring
    g.fillStyle(0xc47a00, 1).fillCircle(c, c, 15);
    // Gold body
    g.fillStyle(0xffc233, 1).fillCircle(c, c, 13);
    // Inner bright
    g.fillStyle(0xffd860, 1).fillCircle(c - 1, c - 1, 10);
    // Innermost
    g.fillStyle(0xffefb0, 1).fillCircle(c - 2, c - 2, 6);
    // Sparkle
    g.fillStyle(0xffffff, 0.95).fillCircle(c - 5, c - 5, 2);
    g.generateTexture('coin', S, S);
    g.destroy();
  }

  // Hazard — sharp thin spikes with dark base
  private makeHazard() {
    const W = 64, H = 26;
    const g = this.add.graphics();
    // Base bar
    g.fillStyle(0x8b0a0a, 1).fillRect(0, H - 3, W, 3);
    // Main spikes
    g.fillStyle(0xf03030, 1);
    for (let x = 0; x < W; x += 16) {
      g.fillTriangle(x, H - 3, x + 8, 1, x + 16, H - 3);
    }
    // Highlight side
    g.fillStyle(0xff8585, 1);
    for (let x = 0; x < W; x += 16) {
      g.fillTriangle(x + 5, H - 3, x + 8, 6, x + 11, H - 3);
    }
    g.generateTexture('hazard', W, H);
    g.destroy();
  }

  // Goal — concentric rings, subtle aura
  private makeGoal() {
    const W = 100, H = 140, cx = W / 2, cy = H / 2;
    const g = this.add.graphics();
    // Soft aura
    g.fillStyle(0xffffff, 0.08).fillCircle(cx, cy, 52);
    g.fillStyle(0xffffff, 0.14).fillCircle(cx, cy, 40);
    // Rings
    g.lineStyle(5, 0xffffff, 0.95).strokeCircle(cx, cy, 46);
    g.lineStyle(3, 0x9ad4ff, 0.95).strokeCircle(cx, cy, 34);
    g.lineStyle(2, 0xffd166, 1).strokeCircle(cx, cy, 22);
    // Core
    g.fillStyle(0xffffff, 1).fillCircle(cx, cy, 9);
    g.generateTexture('goal', W, H);
    g.destroy();
  }

  private makeParticle() {
    const S = 10;
    const g = this.add.graphics();
    g.fillStyle(0xffffff, 1).fillCircle(S / 2, S / 2, S / 2);
    g.generateTexture('particle', S, S);
    g.destroy();
  }

  // Decorative tree — trunk + layered canopy
  private makeTree() {
    const W = 56, H = 84;
    const g = this.add.graphics();
    // Trunk
    g.fillStyle(0x7a4a22, 1).fillRoundedRect(W / 2 - 4, H - 26, 8, 26, 2);
    // Canopy — 3 layered circles
    g.fillStyle(0x3fa85a, 1);
    g.fillCircle(W / 2 - 13, 44, 16);
    g.fillCircle(W / 2 + 13, 44, 16);
    g.fillCircle(W / 2, 32, 20);
    // Top highlight
    g.fillStyle(0x58c676, 1);
    g.fillCircle(W / 2 - 6, 28, 10);
    g.generateTexture('tree', W, H);
    g.destroy();
  }

  private makeBush() {
    const W = 44, H = 26;
    const g = this.add.graphics();
    g.fillStyle(0x3fa85a, 1);
    g.fillCircle(12, 18, 11);
    g.fillCircle(32, 18, 11);
    g.fillCircle(22, 12, 12);
    g.fillStyle(0x58c676, 1);
    g.fillCircle(18, 12, 6);
    g.generateTexture('bush', W, H);
    g.destroy();
  }
}
"""

FILES["src/game/scenes/LevelScene.ts"] = r"""import Phaser from 'phaser';
import { bus, state } from '../bus';
import type { LevelDef, Theme } from '../types';

const WORLD_H = 540;

const THEMES: Record<Theme, {
  skyTop: number; skyBottom: number; hill1: number; hill2: number; platform: number;
}> = {
  day:    { skyTop: 0x9cd4ff, skyBottom: 0xdff0ff, hill1: 0xc8e8d8, hill2: 0xa8d8c0, platform: 0x54cc4a },
  sunset: { skyTop: 0xffc6a8, skyBottom: 0xffe8d0, hill1: 0xffd8b8, hill2: 0xffc0a0, platform: 0xff9855 },
  forest: { skyTop: 0xb8e8d8, skyBottom: 0xe8f8f0, hill1: 0xa8dcc8, hill2: 0x88c8b0, platform: 0x4eb85a },
  candy:  { skyTop: 0xffd0e8, skyBottom: 0xfff4fa, hill1: 0xffd8ec, hill2: 0xffb8dc, platform: 0xd060d0 },
  ocean:  { skyTop: 0x9cd4ff, skyBottom: 0xe8f6ff, hill1: 0xbcdfee, hill2: 0x9cc8e0, platform: 0x4a90e0 },
};

export class LevelScene extends Phaser.Scene {
  private level?: LevelDef;
  private player!: Phaser.Physics.Arcade.Sprite;
  private solids!: Phaser.Physics.Arcade.StaticGroup;
  private coins!: Phaser.Physics.Arcade.StaticGroup;
  private keys!: Record<'left'|'right'|'jump'|'restart', Phaser.Input.Keyboard.Key>;

  private lastGroundedAt = 0;
  private jumpQueuedAt = 0;
  private landedThisFrame = false;

  private virtualLeft = false;
  private virtualRight = false;
  private virtualJump = false;

  private startTime = 0;
  private finished = false;
  private coinsCollected = 0;
  private coinsTotal = 0;

  constructor() { super('Level'); }

  create() {
    if (state.currentLevel) this.loadLevel(state.currentLevel);
    bus.on('level:load', this.loadLevel, this);

    const kb = this.input.keyboard!;
    this.keys = {
      left:    kb.addKey('LEFT'),
      right:   kb.addKey('RIGHT'),
      jump:    kb.addKey('SPACE'),
      restart: kb.addKey('R'),
    };
    this.keys.jump.on('down', () => { this.jumpQueuedAt = this.time.now; });

    bus.on('input:left:down',  () => { this.virtualLeft  = true;  });
    bus.on('input:left:up',    () => { this.virtualLeft  = false; });
    bus.on('input:right:down', () => { this.virtualRight = true;  });
    bus.on('input:right:up',   () => { this.virtualRight = false; });
    bus.on('input:jump:down',  () => {
      this.virtualJump = true;
      this.jumpQueuedAt = this.time.now;
    });
    bus.on('input:jump:up',    () => { this.virtualJump = false; });
  }

  private loadLevel(level: LevelDef): void {
    if (!this.sys?.settings?.active) return;
    if (!this.physics || !this.physics.world) { this.level = level; return; }

    this.level = level;
    this.finished = false;
    this.startTime = this.time.now;
    this.coinsCollected = 0;
    this.coinsTotal = level.coins.length;

    this.children.removeAll();
    this.physics.world.colliders.destroy();
    this.tweens.killAll();
    this.cameras.main.resetFX();

    let maxX = 1200;
    for (const p of level.platforms) maxX = Math.max(maxX, p.x + p.w / 2);
    maxX = Math.max(maxX, level.goal.x + 400);
    const worldW = maxX + 200;
    this.physics.world.setBounds(0, 0, worldW, WORLD_H);

    const theme = THEMES[level.theme];

    // Sky gradient
    const cam = this.cameras.main;
    cam.setBackgroundColor(theme.skyBottom);
    const bg = this.add.graphics().setScrollFactor(0).setDepth(-100);
    bg.fillGradientStyle(theme.skyTop, theme.skyTop, theme.skyBottom, theme.skyBottom, 1);
    bg.fillRect(0, 0, 1280, WORLD_H);

    // Far hills (parallax 0.15)
    const hillLayer = (count: number, yOff: number, w: number, h: number, color: number, alpha: number, px: number) => {
      for (let i = 0; i < count; i++) {
        const hx = i * (worldW / count) + Phaser.Math.Between(-150, 150);
        const hy = WORLD_H + yOff + Phaser.Math.Between(-30, 30);
        const g = this.add.graphics().setScrollFactor(px).setDepth(-85);
        g.fillStyle(color, alpha);
        g.fillEllipse(hx, hy, w, h * 2);
      }
    };
    hillLayer(7, 60, 420, 160, theme.hill1, 0.55, 0.12);
    hillLayer(5, 110, 560, 200, theme.hill2, 0.75, 0.28);

    // Clouds
    for (let i = 0; i < 26; i++) {
      const x = Phaser.Math.Between(0, worldW);
      const y = Phaser.Math.Between(40, 200);
      const w = Phaser.Math.Between(70, 150);
      const h = Phaser.Math.Between(24, 44);
      this.add.ellipse(x, y, w, h, 0xffffff, 0.62)
        .setScrollFactor(0.35).setDepth(-88);
      this.add.ellipse(x + w * 0.3, y - h * 0.35, w * 0.6, h * 0.85, 0xffffff, 0.68)
        .setScrollFactor(0.35).setDepth(-88);
    }

    // Decorations (trees, bushes) — behind platforms
    for (const d of level.decorations) {
      const key = d.kind === 'tree' ? 'tree' : 'bush';
      this.add.image(d.x, d.y + 30, key)
        .setOrigin(0.5, 1)
        .setDepth(-10);
    }

    // Platforms
    this.solids = this.physics.add.staticGroup();
    for (const p of level.platforms) {
      const s = this.solids.create(p.x, p.y, 'platform') as Phaser.Physics.Arcade.Sprite;
      s.setDisplaySize(p.w, p.h).refreshBody();
      s.setTint(theme.platform);
    }

    // Hazards
    for (const h of level.hazards) {
      const s = this.solids.create(h.x, h.y, 'hazard') as Phaser.Physics.Arcade.Sprite;
      s.setDisplaySize(h.w, h.h).refreshBody();
      s.setData('hazard', true);
    }

    // Coins
    this.coins = this.physics.add.staticGroup();
    for (const c of level.coins) {
      const coin = this.coins.create(c.x, c.y, 'coin') as Phaser.Physics.Arcade.Sprite;
      coin.setData('collected', false);
      this.tweens.add({
        targets: coin, y: c.y - 6,
        duration: 1000, yoyo: true, repeat: -1, ease: 'Sine.inOut',
      });
    }
    bus.emit('coins:update', { got: 0, total: this.coinsTotal });

    // Goal
    const goal = this.physics.add.staticSprite(level.goal.x, level.goal.y, 'goal');
    goal.setDisplaySize(level.goal.w, level.goal.h).refreshBody();
    this.tweens.add({
      targets: goal,
      scaleX: goal.scaleX * 1.06, scaleY: goal.scaleY * 1.06,
      duration: 900, yoyo: true, repeat: -1, ease: 'Sine.inOut',
    });

    // Player
    this.player = this.physics.add.sprite(level.spawn.x, level.spawn.y, 'ball');
    this.player.setCircle(40, 8, 8);   // 96px texture, radius 40, offset 8 to centre
    this.player.setBounce(0);
    this.player.setCollideWorldBounds(true);
    this.player.setDragX(1800);
    this.player.setMaxVelocity(420, 1000);
    this.player.setDepth(10);
    this.player.setScale(0.62);        // visually ~60px ball

    // Collisions
    this.physics.add.collider(this.player, this.solids, (_p, obj) => {
      const o = obj as Phaser.GameObjects.GameObject;
      if (o.getData?.('hazard')) this.die();
    });
    this.physics.add.overlap(this.player, this.coins, (_p, coinObj) => {
      this.collectCoin(coinObj as Phaser.Physics.Arcade.Sprite);
    });
    this.physics.add.overlap(this.player, goal, () => this.win());

    // Camera
    cam.setBounds(0, 0, worldW, WORLD_H);
    cam.startFollow(this.player, true, 0.14, 0.14, -200, 40);

    // Intro text
    this.showIntro(level.name);
  }

  private showIntro(name: string): void {
    const cam = this.cameras.main;
    const t = this.add.text(0, 0, name, {
      fontFamily: 'Cairo, Arial, sans-serif',
      fontSize: '64px',
      color: '#ffffff',
      stroke: '#1a3a6a',
      strokeThickness: 10,
      align: 'center',
    })
      .setOrigin(0.5)
      .setScrollFactor(0)
      .setDepth(2000);
    t.setPosition(cam.midPoint.x, cam.midPoint.y - 40);
    t.setAlpha(0);
    t.setScale(0.7);

    this.tweens.add({ targets: t, alpha: 1, scale: 1, duration: 400, ease: 'Back.out' });
    this.tweens.add({
      targets: t, alpha: 0, y: t.y - 60,
      delay: 1100, duration: 500,
      onComplete: () => t.destroy(),
    });
  }

  update() {
    if (!this.level || !this.player || this.finished) return;

    const body = this.player.body as Phaser.Physics.Arcade.Body;
    const onGround = body.blocked.down;
    const now = this.time.now;

    if (onGround) this.lastGroundedAt = now;

    const SPEED = 320;
    const JUMP = -680;
    const COYOTE = 130;
    const BUFFER = 140;

    const wantLeft = this.keys.left.isDown || this.virtualLeft;
    const wantRight = this.keys.right.isDown || this.virtualRight;

    if (wantLeft && !wantRight) this.player.setVelocityX(-SPEED);
    else if (wantRight && !wantLeft) this.player.setVelocityX(SPEED);

    const canJump = now - this.lastGroundedAt < COYOTE;
    const wantsJump = now - this.jumpQueuedAt < BUFFER;
    if (wantsJump && canJump) {
      this.player.setVelocityY(JUMP);
      this.jumpQueuedAt = 0;
      this.lastGroundedAt = -1000;
      this.burstParticles(this.player.x, this.player.y + 22, 0xffd166, 8);
      this.player.setScale(0.55, 0.72);
      this.tweens.add({
        targets: this.player, scaleX: 0.62, scaleY: 0.62,
        duration: 240, ease: 'Back.out',
      });
    }

    this.player.rotation += body.velocity.x * 0.0006;

    if (onGround && !this.landedThisFrame && body.velocity.y > 250) {
      this.landedThisFrame = true;
      this.burstParticles(this.player.x, this.player.y + 22, 0xffffff, 6);
    }
    if (!onGround) this.landedThisFrame = false;

    if (Phaser.Input.Keyboard.JustDown(this.keys.restart)) this.die();
    if (this.player.y > WORLD_H + 200) this.die();
  }

  private collectCoin(coin: Phaser.Physics.Arcade.Sprite): void {
    if (coin.getData('collected')) return;
    coin.setData('collected', true);
    coin.disableBody(true, true);
    this.burstParticles(coin.x, coin.y, 0xffd166, 10);
    this.coinsCollected++;
    bus.emit('coins:update', { got: this.coinsCollected, total: this.coinsTotal });
  }

  private burstParticles(x: number, y: number, color: number, count: number): void {
    for (let i = 0; i < count; i++) {
      const a = (Math.PI * 2 * i) / count + Math.random() * 0.6;
      const sp = Phaser.Math.Between(60, 180);
      const p = this.add.image(x, y, 'particle')
        .setTint(color).setDepth(20)
        .setScale(Phaser.Math.FloatBetween(0.6, 1.4));
      this.tweens.add({
        targets: p,
        x: x + Math.cos(a) * sp,
        y: y + Math.sin(a) * sp,
        alpha: 0, scale: 0,
        duration: Phaser.Math.Between(350, 650),
        ease: 'Cubic.out',
        onComplete: () => p.destroy(),
      });
    }
  }

  private die(): void {
    if (!this.level || this.finished) return;
    this.cameras.main.shake(200, 0.008);
    this.burstParticles(this.player.x, this.player.y, 0xff5555, 16);
    bus.emit('level:death', { levelId: this.level.id });
    this.player.setPosition(this.level.spawn.x, this.level.spawn.y);
    this.player.setVelocity(0, 0);
    this.startTime = this.time.now;
  }

  private win(): void {
    if (!this.level || this.finished) return;
    this.finished = true;
    this.player.setVelocity(0, 0);
    this.burstParticles(this.player.x, this.player.y, 0xffd166, 24);
    bus.emit('level:win', {
      levelId: this.level.id,
      timeMs: Math.round(this.time.now - this.startTime),
      coinsCollected: this.coinsCollected,
      coinsTotal: this.coinsTotal,
    });
  }
}
"""

FILES["src/game/levels/index.ts"] = r"""import level001 from './level-001.json';
import level002 from './level-002.json';
import level003 from './level-003.json';
import level004 from './level-004.json';
import level005 from './level-005.json';
import level006 from './level-006.json';
import level007 from './level-007.json';
import level008 from './level-008.json';
import level009 from './level-009.json';
import level010 from './level-010.json';
import type { LevelDef } from '../types';

const levels = [level001, level002, level003, level004, level005,
                level006, level007, level008, level009, level010] as unknown as LevelDef[];

export default levels;
"""

FILES["src/platform/Menu.tsx"] = r"""import { progress } from '../game/progress';

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
"""

FILES["src/platform/LevelSelect.tsx"] = r"""import levels from '../game/levels';
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
"""

FILES["src/platform/TouchControls.tsx"] = r"""import { useEffect, useState } from 'react';
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
"""

FILES["src/platform/GameScreen.tsx"] = r"""import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import PhaserGame from '../game/PhaserGame';
import { bus } from '../game/bus';
import { quranAudio } from '../game/systems/QuranAudio';
import type { Ayah } from '../game/types';
import { TouchControls } from './TouchControls';
import { progress, computeStars } from '../game/progress';
import type { LevelDef, LevelResult, Theme } from '../game/types';

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
"""

FILES["src/App.tsx"] = r"""import { useState } from 'react';
import Menu from './platform/Menu';
import LevelSelect from './platform/LevelSelect';
import GameScreen from './platform/GameScreen';
import levels from './game/levels';
import type { LevelDef } from './game/types';

type Screen = 'menu' | 'select' | 'playing';

export default function App() {
  const [screen, setScreen] = useState<Screen>('menu');
  const [levelIndex, setLevelIndex] = useState(0);
  const level: LevelDef = levels[levelIndex];

  const nextLevel = () => setLevelIndex(i => (i + 1) % levels.length);

  return (
    <div style={{ width: '100%', height: '100vh', overflow: 'hidden' }}>
      {screen === 'menu' && <Menu onStart={() => setScreen('select')} />}
      {screen === 'select' && (
        <LevelSelect
          onPick={(id) => {
            const idx = levels.findIndex(l => l.id === id);
            setLevelIndex(idx === -1 ? 0 : idx);
            setScreen('playing');
          }}
          onBack={() => setScreen('menu')}
        />
      )}
      {screen === 'playing' && (
        <GameScreen
          key={level.id}
          level={level}
          onExit={() => setScreen('select')}
          onNext={nextLevel}
          hasNext={levelIndex < levels.length - 1}
        />
      )}
    </div>
  );
}
"""

# Write all TS/TSX files
for path_str, content in FILES.items():
    p = ROOT / path_str
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  ✅ {path_str}")


# ═══════════════════════════════════════════════════════════════
# 2. Generate the 10 level JSONs
# ═══════════════════════════════════════════════════════════════
print("\n═══ 2/3  Generating levels ═══")

SURAHS = {
    1:  (114, "الناس",     "day"),
    2:  (113, "الفلق",     "sunset"),
    3:  (112, "الإخلاص",   "candy"),
    4:  (111, "المسد",     "forest"),
    5:  (110, "النصر",     "ocean"),
    6:  (109, "الكافرون",  "day"),
    7:  (108, "الكوثر",    "candy"),
    8:  (107, "الماعون",   "sunset"),
    9:  (106, "قريش",      "forest"),
    10: (105, "الفيل",     "ocean"),
}


def make_level(n, surah, name, theme):
    target_w = 8000 + n * 900

    plats = [{"x": 500, "y": 520, "w": 1000, "h": 40}]
    coins = [
        {"x": 250, "y": 460}, {"x": 450, "y": 460},
        {"x": 650, "y": 460}, {"x": 850, "y": 460},
    ]
    decorations = [
        {"x": 300, "y": 490, "kind": "tree"},
        {"x": 700, "y": 490, "kind": "bush"},
    ]
    x, y = 1050, 520

    rhythm = [
        (260, 120, -50), (260, 130, 50), (240, 140, -80), (240, 140, 80),
        (280, 120, -60), (280, 120, 60), (220, 150, -100), (220, 150, 100),
        (300, 120, -40), (300, 120, 40), (280, 140, -70), (280, 140, 70),
        (250, 130, -50), (250, 130, 50), (300, 120, -90), (300, 120, 90),
        (240, 150, -60), (240, 150, 60), (280, 120, -40), (280, 120, 40),
        (260, 140, -80), (260, 140, 80), (300, 130, -50), (300, 130, 50),
    ]

    for i, (w, gap, dy) in enumerate(rhythm):
        nx = x + gap
        ny = max(300, min(520, y + dy))
        h = 40 if ny == 520 else 30
        plats.append({"x": nx + w / 2, "y": ny, "w": w, "h": h})

        coins.append({"x": nx + w / 2, "y": ny - 70})
        if i % 3 == 1:
            coins.append({"x": nx + w / 2 - 60, "y": ny - 110})
            coins.append({"x": nx + w / 2, "y": ny - 130})
            coins.append({"x": nx + w / 2 + 60, "y": ny - 110})
        if i % 4 == 2:
            coins.append({"x": nx + w / 2 - 80, "y": ny - 80})
            coins.append({"x": nx + w / 2 + 80, "y": ny - 80})

        # occasional tree on ground-level platforms
        if ny == 520 and w >= 260 and i % 3 == 0:
            decorations.append({
                "x": int(nx + w / 2),
                "y": int(ny) - 20,
                "kind": "tree" if i % 2 == 0 else "bush",
            })

        x, y = nx + w, ny

    hazards = []
    if n >= 3:
        hazards.append({"x": 2000, "y": 480, "w": 60, "h": 60})
        hazards.append({"x": 2600, "y": 480, "w": 60, "h": 60})
    if n >= 5:
        hazards.append({"x": 3400, "y": 480, "w": 60, "h": 60})
        hazards.append({"x": 4200, "y": 480, "w": 60, "h": 60})
    if n >= 7:
        hazards.append({"x": 5000, "y": 480, "w": 60, "h": 60})
        hazards.append({"x": 5800, "y": 480, "w": 60, "h": 60})
    if n >= 9:
        hazards.append({"x": 6600, "y": 480, "w": 60, "h": 60})
        hazards.append({"x": 7400, "y": 480, "w": 60, "h": 60})

    outro_x = x + 600
    plats.append({"x": outro_x, "y": 520, "w": 1400, "h": 40})
    coins.append({"x": outro_x - 400, "y": 460})
    coins.append({"x": outro_x - 100, "y": 460})
    coins.append({"x": outro_x + 200, "y": 460})
    decorations.append({"x": int(outro_x - 250), "y": 490, "kind": "tree"})
    decorations.append({"x": int(outro_x + 350), "y": 490, "kind": "bush"})

    return {
        "id": f"level-{n:03d}",
        "name": name,
        "theme": theme,
        "surah": surah,
        "spawn": {"x": 100, "y": 400},
        "platforms": plats,
        "hazards": hazards,
        "coins": coins,
        "goal": {"x": outro_x + 500, "y": 460, "w": 100, "h": 140},
        "decorations": decorations,
    }


LD = ROOT / "src" / "game" / "levels"
for n in range(1, 11):
    surah, name, theme = SURAHS[n]
    lvl = make_level(n, surah, name, theme)
    p = LD / f"level-{n:03d}.json"
    p.write_text(json.dumps(lvl, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  ✅ level-{n:03d}.json  {name}  (surah {surah}, {len(lvl['platforms'])} plats, {len(lvl['coins'])} coins)")


# ═══════════════════════════════════════════════════════════════
# 3. Verify
# ═══════════════════════════════════════════════════════════════
print("\n═══ 3/3  Verifying ═══")
r = subprocess.run("npx tsc --noEmit", shell=True, cwd=str(ROOT))
if r.returncode == 0:
    print("  ✅ TypeScript compiles clean")
else:
    print("  ⚠  TypeScript errors above — paste them")

print()
print("=" * 60)
print("✅ Rebuild complete.")
print("=" * 60)
print("""
Next:
  npm run dev

Then test on desktop. If good:
  python scripts/rebuild.py
""")