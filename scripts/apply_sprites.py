"""Fix visual regression — revert platforms to drawn bar, proper backgrounds."""

import pathlib
import shutil
import subprocess
import sys

PROJECT = pathlib.Path(r"C:\Users\amaha\quran-quest")

# ══════════════════════════════════════════════════════
# 1. BootScene — draw platform in code again
# ══════════════════════════════════════════════════════
print("Writing BootScene.ts...")
BS = PROJECT / "src" / "game" / "scenes" / "BootScene.ts"
if BS.exists():
    shutil.copy2(BS, BS.with_suffix(".ts.bak_v4"))

BOOT = '''import Phaser from 'phaser';
import { bus } from '../bus';

const SPRITE_FILES: Record<string, string> = {
  coin:     'sprites/coin.png',
  hazard:   'sprites/hazard.png',
  goal:     'sprites/goal.png',
  tree:     'sprites/tree.png',
  bush:     'sprites/bush.png',
  rock:     'sprites/rock.png',
  signpost: 'sprites/signpost.png',
  bg_1:     'sprites/bg_1.png',
  bg_2:     'sprites/bg_2.png',
};

export class BootScene extends Phaser.Scene {
  constructor() { super('Boot'); }

  preload() {
    for (const [key, path] of Object.entries(SPRITE_FILES)) {
      this.load.image(key, path);
    }
  }

  create() {
    this.makeBall();
    this.makePlatform();
    this.makeParticle();
    // Fallbacks for file-loaded sprites
    this.ensure('coin',   () => this.makeCoin());
    this.ensure('hazard', () => this.makeHazard());
    this.ensure('goal',   () => this.makeGoal());
    bus.emit('scene:ready');
    this.scene.start('Level');
  }

  private ensure(key: string, fallback: () => void) {
    if (!this.textures.exists(key)) fallback();
  }

  // Red ball
  private makeBall() {
    const S = 96, c = S / 2, r = 40;
    const g = this.add.graphics();
    g.fillStyle(0xd63535, 1).fillCircle(c, c, r);
    g.fillStyle(0xe94a4a, 1).fillCircle(c - 1, c - 1, r - 2);
    g.fillStyle(0xf55f5f, 1).fillCircle(c - 3, c - 3, r - 8);
    g.fillStyle(0xfc7a7a, 1).fillCircle(c - 6, c - 6, r - 15);
    g.fillStyle(0xffa0a0, 1).fillCircle(c - 10, c - 10, r - 22);
    g.fillStyle(0xffffff, 0.9).fillCircle(c - r * 0.4, c - r * 0.45, r * 0.14);
    g.generateTexture('ball', S, S);
    g.destroy();
  }

  // Platform — smooth green-and-dirt bar, drawn in code (no sprite cropping issues)
  private makePlatform() {
    const W = 64, H = 40;
    const g = this.add.graphics();
    // Dirt body
    g.fillStyle(0x8b5a2b, 1).fillRect(0, 8, W, H - 8);
    // Dirt shadow at bottom
    g.fillStyle(0x5c3a14, 1).fillRect(0, H - 6, W, 6);
    // Grass top
    g.fillStyle(0x6cc24a, 1).fillRect(0, 0, W, 8);
    // Grass highlight
    g.fillStyle(0x8ee06b, 1).fillRect(0, 0, W, 3);
    // Grass tufts
    g.fillStyle(0x5cb03c, 1);
    for (let x = 4; x < W - 4; x += 12) {
      g.fillTriangle(x, 0, x + 3, -3, x + 6, 0);
    }
    // Dark outline
    g.lineStyle(2, 0x3a1f08, 0.9).strokeRect(1, 1, W - 2, H - 2);
    g.generateTexture('platform', W, H);
    g.destroy();
  }

  private makeParticle() {
    const S = 10;
    const g = this.add.graphics();
    g.fillStyle(0xffffff, 1).fillCircle(S / 2, S / 2, S / 2);
    g.generateTexture('particle', S, S);
    g.destroy();
  }

  private makeCoin() {
    const S = 44, c = S / 2;
    const g = this.add.graphics();
    g.fillStyle(0xffc233, 1).fillCircle(c, c, 13);
    g.fillStyle(0xffe066, 1).fillCircle(c - 2, c - 2, 9);
    g.generateTexture('coin', S, S);
    g.destroy();
  }

  private makeHazard() {
    const W = 64, H = 26;
    const g = this.add.graphics();
    g.fillStyle(0xf03030, 1);
    for (let x = 0; x < W; x += 16) g.fillTriangle(x, H, x + 8, 1, x + 16, H);
    g.generateTexture('hazard', W, H);
    g.destroy();
  }

  private makeGoal() {
    const W = 100, H = 140, cx = W / 2, cy = H / 2;
    const g = this.add.graphics();
    g.lineStyle(5, 0xffffff, 0.95).strokeCircle(cx, cy, 46);
    g.lineStyle(3, 0x9ad4ff, 0.95).strokeCircle(cx, cy, 34);
    g.fillStyle(0xffffff, 1).fillCircle(cx, cy, 9);
    g.generateTexture('goal', W, H);
    g.destroy();
  }
}
'''
BS.write_text(BOOT, encoding="utf-8")
print("  OK  BootScene.ts")


# ══════════════════════════════════════════════════════
# 2. LevelScene — regular sprites, proper backgrounds
# ══════════════════════════════════════════════════════
print("\nWriting LevelScene.ts...")
LS = PROJECT / "src" / "game" / "scenes" / "LevelScene.ts"
if LS.exists():
    shutil.copy2(LS, LS.with_suffix(".ts.bak_v4"))

LEVEL = r'''import Phaser from 'phaser';
import { bus, state } from '../bus';
import type { LevelDef, Theme } from '../types';

const WORLD_H = 540;

const THEMES: Record<Theme, { skyTop: number; skyBottom: number; hill1: number; hill2: number }> = {
  day:    { skyTop: 0x9cd4ff, skyBottom: 0xdff0ff, hill1: 0xc8e8d8, hill2: 0xa8d8c0 },
  sunset: { skyTop: 0xffc6a8, skyBottom: 0xffe8d0, hill1: 0xffd8b8, hill2: 0xffc0a0 },
  forest: { skyTop: 0xb8e8d8, skyBottom: 0xe8f8f0, hill1: 0xa8dcc8, hill2: 0x88c8b0 },
  candy:  { skyTop: 0xffd0e8, skyBottom: 0xfff4fa, hill1: 0xffd8ec, hill2: 0xffb8dc },
  ocean:  { skyTop: 0x9cd4ff, skyBottom: 0xe8f6ff, hill1: 0xbcdfee, hill2: 0x9cc8e0 },
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

  private startTime = 0;
  private finished = false;
  private coinsCollected = 0;
  private coinsTotal = 0;

  private parallaxImages: { img: Phaser.GameObjects.Image; factor: number }[] = [];

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
    bus.on('input:jump:down',  () => { this.jumpQueuedAt = this.time.now; });

    // Position-based parallax each frame
    this.events.on(Phaser.Scenes.Events.UPDATE, () => {
      const camX = this.cameras.main.scrollX;
      for (const p of this.parallaxImages) {
        p.img.x = -camX * p.factor;
      }
    });
  }

  private loadLevel(level: LevelDef): void {
    if (!this.sys?.settings?.active) return;
    if (!this.physics || !this.physics.world) { this.level = level; return; }

    this.level = level;
    this.finished = false;
    this.startTime = this.time.now;
    this.coinsCollected = 0;
    this.coinsTotal = level.coins.length;
    this.parallaxImages = [];

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
    const cam = this.cameras.main;
    cam.setBackgroundColor(theme.skyBottom);

    // ── Sky gradient ──────────────────────────────────
    const sky = this.add.graphics().setScrollFactor(0).setDepth(-200);
    sky.fillGradientStyle(theme.skyTop, theme.skyTop, theme.skyBottom, theme.skyBottom, 1);
    sky.fillRect(0, 0, 1280, WORLD_H);

    // ── Background image layer 1 (single, wide, no tiling) ──
    if (this.textures.exists('bg_1')) {
      const img = this.add.image(0, WORLD_H / 2, 'bg_1')
        .setOrigin(0, 0.5)
        .setScrollFactor(0)
        .setDepth(-150);
      // Scale to fit viewport height, keep aspect
      const scale = (WORLD_H * 1.1) / img.height;
      img.setScale(scale);
      img.setAlpha(0.7);
      // Store for parallax
      this.parallaxImages.push({ img, factor: 0.15 });
    }

    // ── Background image layer 2 (nearer, faster parallax) ──
    if (this.textures.exists('bg_2')) {
      const img = this.add.image(0, WORLD_H / 2 + 40, 'bg_2')
        .setOrigin(0, 0.5)
        .setScrollFactor(0)
        .setDepth(-140);
      const scale = (WORLD_H * 1.0) / img.height;
      img.setScale(scale);
      img.setAlpha(0.85);
      this.parallaxImages.push({ img, factor: 0.35 });
    }

    // ── Parallax hills (drawn) ────────────────────────
    const hillLayer = (count: number, yOff: number, w: number, h: number, color: number, alpha: number, px: number) => {
      for (let i = 0; i < count; i++) {
        const hx = i * (worldW / count) + Phaser.Math.Between(-150, 150);
        const hy = WORLD_H + yOff + Phaser.Math.Between(-30, 30);
        const g = this.add.graphics().setScrollFactor(px).setDepth(-120);
        g.fillStyle(color, alpha);
        g.fillEllipse(hx, hy, w, h * 2);
      }
    };
    hillLayer(7, 80, 420, 160, theme.hill1, 0.5, 0.12);
    hillLayer(5, 130, 560, 200, theme.hill2, 0.7, 0.28);

    // ── Decorations (small) ──────────────────────────
    for (const d of level.decorations) {
      const key = d.kind === 'tree' ? 'tree' : 'bush';
      if (!this.textures.exists(key)) continue;
      const img = this.add.image(d.x, d.y + 25, key)
        .setOrigin(0.5, 1)
        .setDepth(-10);
      if (d.kind === 'tree') img.setScale(0.45);
      else img.setScale(0.55);
    }

    // ── Platforms (regular sprites, stretched) ────────
    this.solids = this.physics.add.staticGroup();
    for (const p of level.platforms) {
      const s = this.solids.create(p.x, p.y, 'platform') as Phaser.Physics.Arcade.Sprite;
      s.setDisplaySize(p.w, Math.max(p.h, 26)).refreshBody();
    }

    // ── Hazards ──────────────────────────────────────
    for (const h of level.hazards) {
      const s = this.solids.create(h.x, h.y, 'hazard') as Phaser.Physics.Arcade.Sprite;
      s.setDisplaySize(h.w, Math.max(h.h, 26)).refreshBody();
      s.setData('hazard', true);
    }

    // ── Coins (34×34) ────────────────────────────────
    this.coins = this.physics.add.staticGroup();
    for (const c of level.coins) {
      const coin = this.coins.create(c.x, c.y, 'coin') as Phaser.Physics.Arcade.Sprite;
      coin.setDisplaySize(30, 30);
      coin.refreshBody();
      coin.setData('collected', false);
      this.tweens.add({
        targets: coin, y: c.y - 5,
        duration: 1000, yoyo: true, repeat: -1, ease: 'Sine.inOut',
      });
    }
    bus.emit('coins:update', { got: 0, total: this.coinsTotal });

    // ── Goal portal ──────────────────────────────────
    const goal = this.physics.add.staticSprite(level.goal.x, level.goal.y, 'goal');
    goal.setDisplaySize(80, 110).refreshBody();
    goal.setDepth(2);
    this.tweens.add({
      targets: goal,
      scaleX: goal.scaleX * 1.06, scaleY: goal.scaleY * 1.06,
      duration: 900, yoyo: true, repeat: -1, ease: 'Sine.inOut',
    });

    // ── Player ───────────────────────────────────────
    this.player = this.physics.add.sprite(level.spawn.x, level.spawn.y, 'ball');
    this.player.setCircle(40, 8, 8);
    this.player.setBounce(0);
    this.player.setCollideWorldBounds(true);
    this.player.setDragX(1800);
    this.player.setMaxVelocity(420, 1000);
    this.player.setDepth(10);
    this.player.setScale(0.62);

    // ── Collisions ───────────────────────────────────
    this.physics.add.collider(this.player, this.solids, (_p, obj) => {
      const o = obj as Phaser.GameObjects.GameObject;
      if (o.getData?.('hazard')) this.die();
    });
    this.physics.add.overlap(this.player, this.coins, (_p, coinObj) => {
      this.collectCoin(coinObj as Phaser.Physics.Arcade.Sprite);
    });
    this.physics.add.overlap(this.player, goal, () => this.win());

    // ── Camera ───────────────────────────────────────
    cam.setBounds(0, 0, worldW, WORLD_H);
    cam.startFollow(this.player, true, 0.14, 0.14, -200, 40);

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
      .setOrigin(0.5).setScrollFactor(0).setDepth(2000);
    t.setPosition(cam.midPoint.x, cam.midPoint.y - 40);
    t.setAlpha(0).setScale(0.7);
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
'''
LS.write_text(LEVEL, encoding="utf-8")
print("  OK  LevelScene.ts")


# ══════════════════════════════════════════════════════
# 3. Build
# ══════════════════════════════════════════════════════
print("\nBuilding...")
r = subprocess.run("npm run build", shell=True, cwd=str(PROJECT))
if r.returncode != 0:
    print("X  build failed")
    sys.exit(1)

print("\n" + "=" * 55)
print("Done.")
print("=" * 55)
print("""
Changes:
  Platform: green grass + brown dirt bar, drawn in code (reliable)
  Background: single wide image per layer, position-based parallax (no tiling seams)
  Clouds: single bg image, scaled to fit viewport height, no seam
  Coins: 30x30 px
  Trees/bushes: scaled 0.45 / 0.55
  Portal: 80x110

Next:  npm run dev
""")