"""Full reset of quran-quest game files.
Overwrites all critical files with known-good working versions.
Run from inside quran-quest."""
import pathlib
import shutil
import sys

ROOT = pathlib.Path(".").resolve()
if not (ROOT / "package.json").exists():
    print("❌ Run this from inside quran-quest folder")
    sys.exit(1)

# Back up everything into a timestamped folder first
backup_dir = ROOT / "src" / "_backup_before_reset"
backup_dir.mkdir(parents=True, exist_ok=True)


def backup(p: pathlib.Path):
    if p.exists():
        rel = p.relative_to(ROOT)
        dst = backup_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)


FILES = {}


FILES["src/game/types.ts"] = '''// src/game/types.ts
export type PageAudio = { page: number; file: string };

export type Rect = { x: number; y: number; w: number; h: number };

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


FILES["src/game/bus.ts"] = '''// src/game/bus.ts
import Phaser from 'phaser';
import type { LevelDef } from './types';

export const bus = new Phaser.Events.EventEmitter();

export const state = {
  currentLevel: null as LevelDef | null,
};
'''


FILES["src/game/progress.ts"] = '''// src/game/progress.ts
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
  } catch { return {}; }
}

function save(p: ProgressMap): void {
  try { localStorage.setItem(KEY, JSON.stringify(p)); } catch {}
}

export const progress = {
  get(levelId: string): LevelProgress | undefined {
    return load()[levelId];
  },
  record(levelId: string, stars: number, timeMs: number, coinsCollected: number): LevelProgress {
    const all = load();
    const prev = all[levelId];
    const cs = Math.max(0, Math.min(3, stars)) as 0 | 1 | 2 | 3;
    const next: LevelProgress = {
      stars: prev ? (Math.max(prev.stars, cs) as 0 | 1 | 2 | 3) : cs,
      bestTimeMs: prev ? Math.min(prev.bestTimeMs, timeMs) : timeMs,
      coinsCollected: prev ? Math.max(prev.coinsCollected, coinsCollected) : coinsCollected,
      completed: true,
    };
    all[levelId] = next;
    save(all);
    return next;
  },
  clear(): void { localStorage.removeItem(KEY); },
};

export function computeStars(coinsGot: number, coinsTotal: number, timeMs: number): number {
  let s = 1;
  if (coinsTotal > 0 && coinsGot / coinsTotal >= 0.6) s++;
  if (timeMs < 60000) s++;
  return s;
}
'''


FILES["src/game/systems/QuranAudio.ts"] = '''// src/game/systems/QuranAudio.ts
import type { PageAudio } from '../types';

export class QuranAudio extends EventTarget {
  private el = new Audio();
  private queue: PageAudio[] = [];
  private index = 0;
  private started = false;
  private armed = false;

  constructor() {
    super();
    this.el.volume = 0.5;
    this.el.preload = 'auto';
    this.el.addEventListener('ended', () => this.next());
    this.el.addEventListener('play',  () => this.dispatchEvent(new Event('play')));
    this.el.addEventListener('pause', () => this.dispatchEvent(new Event('pause')));
  }

  load(pages: PageAudio[]): void {
    this.queue = pages;
    this.index = 0;
  }

  async start(): Promise<void> {
    if (!this.queue.length) return;
    this.started = true;
    this.armed = true;
    await this.playCurrent();
  }

  async resume(): Promise<void> {
    if (!this.started || !this.armed) return this.start();
    try { await this.el.play(); } catch (e) { console.warn('resume blocked:', e); }
  }

  pause(): void { try { this.el.pause(); } catch {} }

  setVolume(v: number): void {
    this.el.volume = Math.max(0, Math.min(1, v));
  }

  get current(): PageAudio | undefined { return this.queue[this.index]; }

  private async playCurrent(): Promise<void> {
    const cur = this.current;
    if (!cur) return;
    this.el.src = cur.file.startsWith('/') ? cur.file : '/' + cur.file;
    try {
      await this.el.play();
      this.dispatchEvent(new CustomEvent<PageAudio>('page', { detail: cur }));
    } catch {
      // Autoplay blocked or file missing — silent, no crash.
      this.dispatchEvent(new CustomEvent<PageAudio>('page', { detail: cur }));
    }
  }

  private next(): void {
    if (this.queue.length === 0) return;
    this.index = (this.index + 1) % this.queue.length;
    void this.playCurrent();
  }
}

export const quranAudio = new QuranAudio();
'''


FILES["src/game/PhaserGame.tsx"] = '''// src/game/PhaserGame.tsx
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
      pixelArt: false,
      roundPixels: false,
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
    const t = window.setTimeout(() => bus.emit('level:load', level), 0);
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


FILES["src/game/scenes/BootScene.ts"] = '''// src/game/scenes/BootScene.ts
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

  private makeBall() {
    const S = 64, c = S / 2;
    const g = this.add.graphics();
    g.fillStyle(0x000000, 0.15).fillCircle(c, c + 3, 26);
    g.fillStyle(0xffcc33, 1).fillCircle(c, c, 26);
    g.fillStyle(0xff4433, 1).fillCircle(c, c, 24);
    g.fillStyle(0xff7755, 1).fillCircle(c - 3, c - 3, 20);
    g.fillStyle(0xffaa88, 1).fillCircle(c - 7, c - 7, 12);
    g.fillStyle(0xffffff, 0.9).fillCircle(c - 9, c - 9, 6);
    g.lineStyle(3, 0xffffff, 1).strokeCircle(c, c, 24);
    g.generateTexture('ball', S, S);
    g.destroy();
  }

  private makePlatform() {
    const W = 64, H = 32;
    const g = this.add.graphics();
    g.fillStyle(0xdddddd, 1).fillRoundedRect(0, 0, W, H, 10);
    g.fillStyle(0xffffff, 1).fillRoundedRect(0, 0, W, 10, { tl: 10, tr: 10, bl: 0, br: 0 });
    g.fillStyle(0x888888, 1).fillRoundedRect(0, H - 10, W, 10, { tl: 0, tr: 0, bl: 10, br: 10 });
    g.lineStyle(3, 0x444444, 1).strokeRoundedRect(1.5, 1.5, W - 3, H - 3, 10);
    g.generateTexture('platform', W, H);
    g.destroy();
  }

  private makeCoin() {
    const S = 36, c = S / 2;
    const g = this.add.graphics();
    g.fillStyle(0x000000, 0.2).fillCircle(c, c + 2, 14);
    g.fillStyle(0xcc8800, 1).fillCircle(c, c, 14);
    g.fillStyle(0xffcc33, 1).fillCircle(c, c - 1, 12);
    g.fillStyle(0xffe888, 1).fillCircle(c - 3, c - 3, 6);
    g.fillStyle(0xffffff, 0.9).fillCircle(c - 5, c - 5, 3);
    g.lineStyle(2, 0x885500, 1).strokeCircle(c, c, 14);
    g.generateTexture('coin', S, S);
    g.destroy();
  }

  private makeHazard() {
    const W = 32, H = 32;
    const g = this.add.graphics();
    g.fillStyle(0xaa1010, 1).fillRect(0, H - 6, W, 6);
    g.fillStyle(0xff3333, 1);
    for (let x = 0; x < W; x += 16) {
      g.fillTriangle(x, H, x + 8, 2, x + 16, H);
    }
    g.fillStyle(0xff8888, 1);
    for (let x = 0; x < W; x += 16) {
      g.fillTriangle(x + 5, H, x + 8, 6, x + 11, H);
    }
    g.lineStyle(2, 0x661010, 1).strokeRect(1, 1, W - 2, H - 2);
    g.generateTexture('hazard', W, H);
    g.destroy();
  }

  private makeGoal() {
    const W = 80, H = 120;
    const cx = W / 2, cy = H / 2;
    const g = this.add.graphics();
    g.fillStyle(0xff88cc, 0.25).fillCircle(cx, cy, 52);
    g.fillStyle(0x66ccff, 0.5).fillCircle(cx, cy, 40);
    g.fillStyle(0xffdd66, 0.85).fillCircle(cx, cy, 28);
    g.fillStyle(0xffffff, 1).fillCircle(cx, cy, 16);
    g.lineStyle(4, 0xffffff, 1).strokeCircle(cx, cy, 40);
    g.lineStyle(2, 0xff88cc, 1).strokeCircle(cx, cy, 52);
    g.generateTexture('goal', W, H);
    g.destroy();
  }

  private makeParticle() {
    const S = 8;
    const g = this.add.graphics();
    g.fillStyle(0xffffff, 1).fillCircle(S / 2, S / 2, S / 2);
    g.generateTexture('particle', S, S);
    g.destroy();
  }
}
'''


FILES["src/game/scenes/LevelScene.ts"] = r'''// src/game/scenes/LevelScene.ts
import Phaser from 'phaser';
import { bus, state } from '../bus';
import type { LevelDef, Theme } from '../types';

const WORLD_H = 540;
const CAM_W = 960;

const THEMES: Record<Theme, { skyTop: number; skyBottom: number; platform: number }> = {
  day:    { skyTop: 0x4aa8ff, skyBottom: 0xc8e8ff, platform: 0x4ac84a },
  sunset: { skyTop: 0xff8866, skyBottom: 0xffd8a0, platform: 0xd8884a },
  forest: { skyTop: 0x6ac8a8, skyBottom: 0xd8f0e8, platform: 0x3d8a4a },
  candy:  { skyTop: 0xff8ac8, skyBottom: 0xffe0f0, platform: 0xb050b0 },
  ocean:  { skyTop: 0x4ac8ff, skyBottom: 0xd0f0ff, platform: 0x3a78b8 },
};

export class LevelScene extends Phaser.Scene {
  private level?: LevelDef;
  private player!: Phaser.Physics.Arcade.Sprite;
  private solids!: Phaser.Physics.Arcade.StaticGroup;
  private coins!: Phaser.Physics.Arcade.StaticGroup;
  private keys!: Record<'left' | 'right' | 'jump' | 'restart', Phaser.Input.Keyboard.Key>;

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
    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => {
      bus.off('level:load', this.loadLevel, this);
    });

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

    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => {
      bus.off('input:left:down');
      bus.off('input:left:up');
      bus.off('input:right:down');
      bus.off('input:right:up');
      bus.off('input:jump:down');
      bus.off('input:jump:up');
    });
  }

  private loadLevel(level: LevelDef): void {
    if (!this.sys?.settings?.active) return;
    if (!this.physics || !this.physics.world) {
      this.level = level;
      return;
    }

    this.level = level;
    this.finished = false;
    this.startTime = this.time.now;
    this.coinsCollected = 0;
    this.coinsTotal = (level.coins ?? []).length;

    this.children.removeAll();
    this.physics.world.colliders.destroy();
    this.tweens.killAll();
    this.cameras.main.resetFX();

    let maxX = 1200;
    for (const p of level.platforms) maxX = Math.max(maxX, p.x + p.w / 2);
    maxX = Math.max(maxX, level.goal.x + 400);
    const worldW = maxX + 200;
    this.physics.world.setBounds(0, 0, worldW, WORLD_H);

    const theme = THEMES[level.theme ?? 'day'];
    this.cameras.main.setBackgroundColor(theme.skyBottom);
    const bg = this.add.graphics().setScrollFactor(0).setDepth(-100);
    bg.fillGradientStyle(theme.skyTop, theme.skyTop, theme.skyBottom, theme.skyBottom, 1);
    bg.fillRect(0, 0, CAM_W, WORLD_H);

    for (let i = 0; i < 30; i++) {
      const x = Phaser.Math.Between(0, worldW);
      const y = Phaser.Math.Between(40, 220);
      const w = Phaser.Math.Between(60, 140);
      const h = Phaser.Math.Between(20, 40);
      this.add.ellipse(x, y, w, h, 0xffffff, 0.55).setScrollFactor(0.3).setDepth(-90);
      this.add.ellipse(x + w * 0.3, y - h * 0.3, w * 0.6, h * 0.8, 0xffffff, 0.6)
        .setScrollFactor(0.3).setDepth(-90);
    }

    const pageKey = `page-${String(level.startPage).padStart(3, '0')}`;
    if (this.textures.exists(pageKey)) {
      const img = this.add.image(480, WORLD_H / 2, pageKey)
        .setAlpha(0.28).setScrollFactor(0.4).setDepth(-80);
      const scale = Math.min(500 / img.width, (WORLD_H * 0.85) / img.height);
      img.setScale(scale);
    }

    this.solids = this.physics.add.staticGroup();
    for (const p of level.platforms) {
      const s = this.solids.create(p.x, p.y, 'platform') as Phaser.Physics.Arcade.Sprite;
      s.setDisplaySize(p.w, p.h).refreshBody();
      s.setTint(theme.platform);
    }

    for (const h of level.hazards) {
      const s = this.solids.create(h.x, h.y, 'hazard') as Phaser.Physics.Arcade.Sprite;
      s.setDisplaySize(h.w, h.h).refreshBody();
      s.setData('hazard', true);
    }

    this.coins = this.physics.add.staticGroup();
    for (const c of level.coins ?? []) {
      const coin = this.coins.create(c.x, c.y, 'coin') as Phaser.Physics.Arcade.Sprite;
      coin.setData('collected', false);
      this.tweens.add({
        targets: coin, y: c.y - 6,
        duration: 900, yoyo: true, repeat: -1, ease: 'Sine.inOut',
      });
    }
    bus.emit('coins:update', { got: 0, total: this.coinsTotal });

    const goal = this.physics.add.staticSprite(level.goal.x, level.goal.y, 'goal');
    goal.setDisplaySize(level.goal.w, level.goal.h).refreshBody();
    this.tweens.add({
      targets: goal,
      scaleX: goal.scaleX * 1.10,
      scaleY: goal.scaleY * 1.10,
      duration: 700, yoyo: true, repeat: -1, ease: 'Sine.inOut',
    });

    this.player = this.physics.add.sprite(level.spawn.x, level.spawn.y, 'ball');
    this.player.setCircle(24, 8, 8);
    this.player.setBounce(0);
    this.player.setCollideWorldBounds(true);
    this.player.setDragX(1400);
    this.player.setMaxVelocity(340, 900);
    this.player.setDepth(10);

    this.physics.add.collider(this.player, this.solids, (_p, obj) => {
      const o = obj as Phaser.GameObjects.GameObject;
      if (o.getData?.('hazard')) this.die();
    });
    this.physics.add.overlap(this.player, this.coins, (_p, coinObj) => {
      this.collectCoin(coinObj as Phaser.Physics.Arcade.Sprite);
    });
    this.physics.add.overlap(this.player, goal, () => this.win());

    this.cameras.main.setBounds(0, 0, worldW, WORLD_H);
    this.cameras.main.startFollow(this.player, true, 0.12, 0.12, -260, 40);
    this.cameras.main.setZoom(1280 / 960);

    this.showIntro(level.name ?? level.id);
  }

  private showIntro(name: string): void {
    const cam = this.cameras.main;
    const text = this.add.text(0, 0, name, {
      fontFamily: 'Arial, sans-serif',
      fontSize: '64px',
      color: '#ffffff',
      stroke: '#1a3a6a',
      strokeThickness: 10,
      align: 'center',
    })
      .setOrigin(0.5)
      .setScrollFactor(0)
      .setDepth(2000);
    text.setPosition(cam.midPoint.x, cam.midPoint.y - 40);
    text.setAlpha(0);
    text.setScale(0.7);

    this.tweens.add({
      targets: text, alpha: 1, scale: 1,
      duration: 400, ease: 'Back.out',
    });
    this.tweens.add({
      targets: text, alpha: 0, y: text.y - 60,
      delay: 1100, duration: 500,
      onComplete: () => text.destroy(),
    });
  }

  update() {
    if (!this.level || !this.player || this.finished) return;

    const body = this.player.body as Phaser.Physics.Arcade.Body;
    const onGround = body.blocked.down;
    const now = this.time.now;

    if (onGround) this.lastGroundedAt = now;

    const SPEED = 300;
    const JUMP  = -640;
    const COYOTE_MS = 120;
    const BUFFER_MS = 120;

    const wantLeft  = this.keys.left.isDown  || this.virtualLeft;
    const wantRight = this.keys.right.isDown || this.virtualRight;

    if (wantLeft && !wantRight) this.player.setVelocityX(-SPEED);
    else if (wantRight && !wantLeft) this.player.setVelocityX(SPEED);

    const canJump   = now - this.lastGroundedAt < COYOTE_MS;
    const wantsJump = now - this.jumpQueuedAt   < BUFFER_MS;
    if (wantsJump && canJump) {
      this.player.setVelocityY(JUMP);
      this.jumpQueuedAt = 0;
      this.lastGroundedAt = -1000;
      this.burstParticles(this.player.x, this.player.y + 22, 0xffd166, 8);
      this.player.setScale(0.85, 1.15);
      this.tweens.add({
        targets: this.player, scaleX: 1, scaleY: 1,
        duration: 220, ease: 'Back.out',
      });
    }

    this.player.rotation += body.velocity.x * 0.0005;

    if (onGround && !this.landedThisFrame && body.velocity.y > 200) {
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
    bus.emit('coins:update', {
      got: this.coinsCollected,
      total: this.coinsTotal,
    });
  }

  private burstParticles(x: number, y: number, color: number, count: number): void {
    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 * i) / count + Math.random() * 0.6;
      const speed = Phaser.Math.Between(60, 180);
      const p = this.add.image(x, y, 'particle')
        .setTint(color).setDepth(20)
        .setScale(Phaser.Math.FloatBetween(0.6, 1.4));
      this.tweens.add({
        targets: p,
        x: x + Math.cos(angle) * speed,
        y: y + Math.sin(angle) * speed,
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
'''


FILES["src/platform/TouchControls.tsx"] = '''// src/platform/TouchControls.tsx
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
'''


FILES["src/platform/GameScreen.tsx"] = '''// src/platform/GameScreen.tsx
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
  const [coins, setCoins] = useState({ got: 0, total: 0 });

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
    const onCoins = (e: Event) => {
      const d = (e as CustomEvent<{ got: number; total: number }>).detail;
      setCoins({ got: d.got, total: d.total });
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


FILES["src/platform/LevelSelect.tsx"] = '''// src/platform/LevelSelect.tsx
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
    </div>
  );
}

const wrap: CSSProperties = {
  minHeight: '100vh', padding: '32px 24px 80px',
  display: 'flex', flexDirection: 'column', alignItems: 'center',
  background: 'linear-gradient(180deg, #7ecbff 0%, #bfe5ff 60%, #d8f5c0 100%)',
  overflowY: 'auto',
};
const header: CSSProperties = { textAlign: 'center', marginBottom: 32 };
const title: CSSProperties = {
  fontSize: 'clamp(36px, 6vw, 56px)', margin: 0,
  color: '#1a3a6a', fontWeight: 900,
};
const sub: CSSProperties = {
  fontSize: 18, color: '#4a6a9a', margin: '6px 0 0', fontWeight: 600,
};
const grid: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
  gap: 20, maxWidth: 820, width: '100%',
};
const card: CSSProperties = {
  position: 'relative', display: 'flex', flexDirection: 'column',
  alignItems: 'center', padding: '18px 14px 16px',
  borderRadius: 24, color: '#fff',
  border: '4px solid rgba(255,255,255,0.85)',
  cursor: 'pointer', fontFamily: 'inherit', minHeight: 180,
  transition: 'transform 0.15s ease',
};
const icon: CSSProperties = {
  fontSize: 44, lineHeight: 1, marginBottom: 6,
};
const number: CSSProperties = {
  position: 'absolute', top: -14, left: -14,
  width: 42, height: 42, lineHeight: '42px',
  borderRadius: '50%', background: '#fff',
  color: '#1a3a6a', fontWeight: 900, fontSize: 20,
  textAlign: 'center',
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
  boxShadow: '0 6px 0 #b8d0e0',
  cursor: 'pointer', fontFamily: 'inherit',
};
'''


FILES["src/platform/Menu.tsx"] = '''// src/platform/Menu.tsx
import type { CSSProperties } from 'react';
import { progress } from '../game/progress';

export default function Menu({ onStart }: { onStart: () => void }) {
  return (
    <div style={screen}>
      <div style={content}>
        <div style={mascot}>🎈</div>
        <h1 style={title}>
          <span style={{ color: '#ff6b35' }}>Quran</span>{' '}
          <span style={{ color: '#4a90e2' }}>Quest</span>
        </h1>
        <p className="ar" style={subtitle}>ارْكض · اقفِز · اسْتَمِع</p>

        <button onClick={onStart} style={startBtn}>
          ▶ Let's Play!
        </button>

        <p style={hint}>
          ← → move · SPACE jump · R restart
        </p>

        <button
          onClick={() => {
            if (window.confirm('Reset all stars and progress?')) {
              progress.clear();
              window.location.reload();
            }
          }}
          style={resetBtn}
        >
          🔄 Reset progress
        </button>
      </div>
    </div>
  );
}

const screen: CSSProperties = {
  position: 'relative', width: '100%', height: '100vh',
  background: 'linear-gradient(180deg, #7ecbff 0%, #bfe5ff 45%, #ffe5a8 100%)',
  display: 'grid', placeItems: 'center', overflow: 'hidden',
};
const content: CSSProperties = { textAlign: 'center', padding: 24 };
const mascot: CSSProperties = {
  fontSize: 130, lineHeight: 1,
  filter: 'drop-shadow(0 8px 20px rgba(255,80,80,0.35))',
};
const title: CSSProperties = {
  fontSize: 'clamp(48px, 10vw, 92px)',
  margin: '12px 0 4px', letterSpacing: -1, fontWeight: 900,
  textShadow: '0 4px 0 rgba(255,255,255,0.9)',
};
const subtitle: CSSProperties = {
  fontSize: 'clamp(20px, 3vw, 28px)',
  margin: '8px 0 32px', color: '#3a5a8a', fontWeight: 700,
};
const startBtn: CSSProperties = {
  padding: '20px 52px', fontSize: 28, fontWeight: 800,
  color: '#fff',
  background: 'linear-gradient(180deg, #ff9a3c 0%, #ff6b35 100%)',
  borderRadius: 999,
  boxShadow: '0 6px 0 #c4451a, 0 12px 28px rgba(255,107,53,0.45)',
  border: 'none', cursor: 'pointer', fontFamily: 'inherit',
};
const hint: CSSProperties = {
  marginTop: 40, fontSize: 14, color: '#3a5a8a', opacity: 0.75, fontWeight: 600,
};
const resetBtn: CSSProperties = {
  marginTop: 18, padding: '8px 18px', fontSize: 14, fontWeight: 700,
  color: '#3a5a8a',
  background: 'rgba(255,255,255,0.7)',
  borderRadius: 999,
  border: '2px solid rgba(255,255,255,0.9)',
  cursor: 'pointer', fontFamily: 'inherit',
};
'''


FILES["src/App.tsx"] = '''// src/App.tsx
import { useState } from 'react';
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
      {screen === 'menu' && (
        <Menu onStart={() => setScreen('select')} />
      )}
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
'''


FILES["src/index.css"] = '''/* src/index.css */
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, #root {
  height: 100%;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Cairo', system-ui, -apple-system, sans-serif;
  background: #a8d8ff;
  color: #1a2a4a;
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
}

button {
  font-family: inherit;
  cursor: pointer;
  border: none;
  background: none;
  color: inherit;
  -webkit-tap-highlight-color: transparent;
}

button:active { transform: translateY(2px); }

canvas {
  display: block;
  outline: none;
  user-select: none;
  -webkit-user-select: none;
  touch-action: none;
}
'''


# ── Write everything ──────────────────────────────────
print("Writing files...\n")
written = 0
for path_str, content in FILES.items():
    p = ROOT / path_str
    backup(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  ✅ {path_str}")
    written += 1

print(f"\n🎉 Wrote {written} files.")
print(f"💾 Old versions backed up to: {backup_dir}")
print("\nNow:")
print("  1. Stop the dev server (Ctrl+C)")
print("  2. npm run dev -- --host")
print("  3. Reload the browser")
print("\nIf something still fails, paste the FULL red error from the browser console.")