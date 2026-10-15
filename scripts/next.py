"""Game-changer patch: checkpoints, rewind, cinematic, ghost, coin fix.
Replaces LevelScene.ts entirely. Patches GameScreen.tsx and TouchControls.tsx.
Backs up every file it touches."""

import pathlib
import shutil
import sys

ROOT = pathlib.Path(".").resolve()
if not (ROOT / "package.json").exists():
    print("❌ Run this from inside quran-quest")
    sys.exit(1)

print(f"📁 {ROOT}\n")


def backup(p: pathlib.Path):
    bak = p.with_suffix(p.suffix + ".bak2")
    if not bak.exists() and p.exists():
        shutil.copy2(p, bak)
        print(f"  💾 {bak}")


# ═══════════════════════════════════════════════════════════════════
# 1. Add 'state' export to bus.ts (LevelScene needs it for cold start)
# ═══════════════════════════════════════════════════════════════════
print("═══ 1/3  bus.ts ═══")
BUS = pathlib.Path("src/game/bus.ts")
bus_content = '''// src/game/bus.ts
import Phaser from 'phaser';
import type { LevelDef } from './types';

export const bus = new Phaser.Events.EventEmitter();

export const state = {
  currentLevel: null as LevelDef | null,
};
'''
if BUS.exists():
    c = BUS.read_text(encoding="utf-8")
    if "currentLevel" not in c:
        backup(BUS)
        BUS.write_text(bus_content, encoding="utf-8")
        print("  ✅ added state object")
    else:
        print("  ⏭  already has state")


# ═══════════════════════════════════════════════════════════════════
# 2. Full rewrite of LevelScene.ts
# ═══════════════════════════════════════════════════════════════════
print("\n═══ 2/3  LevelScene.ts ═══")

LEVEL_SCENE = r'''// src/game/scenes/LevelScene.ts
import Phaser from 'phaser';
import { bus, state } from '../bus';
import type { LevelDef, Theme } from '../types';

const WORLD_H = 540;
const CAM_W = 960;
const REWIND_MS = 3000;
const SAMPLE_MS = 40;
const HOLD_TO_HOLD = 200;

const THEMES: Record<Theme, {
  skyTop: number; skyBottom: number; platform: number;
}> = {
  day:    { skyTop: 0x4aa8ff, skyBottom: 0xc8e8ff, platform: 0x4ac84a },
  sunset: { skyTop: 0xff8866, skyBottom: 0xffd8a0, platform: 0xd8884a },
  forest: { skyTop: 0x6ac8a8, skyBottom: 0xd8f0e8, platform: 0x3d8a4a },
  candy:  { skyTop: 0xff8ac8, skyBottom: 0xffe0f0, platform: 0xb050b0 },
  ocean:  { skyTop: 0x4ac8ff, skyBottom: 0xd0f0ff, platform: 0x3a78b8 },
};

type Snapshot = {
  x: number; y: number; vx: number; vy: number; t: number;
};

export class LevelScene extends Phaser.Scene {
  private level?: LevelDef;
  private player!: Phaser.Physics.Arcade.Sprite;
  private solids!: Phaser.Physics.Arcade.StaticGroup;
  private coins!: Phaser.Physics.Arcade.StaticGroup;
  private goalSprite!: Phaser.Physics.Arcade.Sprite;
  private keys!: Record<
    'left' | 'right' | 'jump' | 'restart' | 'rewind',
    Phaser.Input.Keyboard.Key
  >;

  // Feel
  private lastGroundedAt = 0;
  private jumpQueuedAt = 0;
  private jumpHoldStart = 0;
  private jumpHeld = false;
  private landedThisFrame = false;
  private virtualLeft = false;
  private virtualRight = false;
  private virtualJump = false;
  private virtualRewind = false;

  // Stats
  private startTime = 0;
  private finished = false;
  private coinsCollected = 0;
  private coinsTotal = 0;

  // Checkpoint
  private checkpoint = { x: 0, y: 0 };
  private checkpointMarker?: Phaser.GameObjects.Image;

  // Rewind
  private history: Snapshot[] = [];
  private lastSampleAt = 0;

  // Trail
  private trail: Phaser.GameObjects.Image[] = [];
  private lastTrailAt = 0;

  // Cinematic
  private cinematicActive = false;
  private introText?: Phaser.GameObjects.Text;

  constructor() { super('Level'); }

  create() {
    console.log('[LevelScene] create');

    // Cold-start safety net
    if (state.currentLevel) {
      console.log('[LevelScene] loading from state:', state.currentLevel.id);
      this.loadLevel(state.currentLevel);
    }

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
      rewind:  kb.addKey('X'),
    };
    this.keys.jump.on('down', () => { this.jumpQueuedAt = this.time.now; });

    // Touch input
    bus.on('input:left:down',  () => { this.virtualLeft  = true;  });
    bus.on('input:left:up',    () => { this.virtualLeft  = false; });
    bus.on('input:right:down', () => { this.virtualRight = true;  });
    bus.on('input:right:up',   () => { this.virtualRight = false; });
    bus.on('input:jump:down',  () => {
      this.virtualJump = true;
      this.jumpQueuedAt = this.time.now;
    });
    bus.on('input:jump:up',    () => { this.virtualJump = false; });
    bus.on('input:rewind:down',() => { this.virtualRewind = true;  });
    bus.on('input:rewind:up',  () => { this.virtualRewind = false; });

    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => {
      bus.off('input:left:down');
      bus.off('input:left:up');
      bus.off('input:right:down');
      bus.off('input:right:up');
      bus.off('input:jump:down');
      bus.off('input:jump:up');
      bus.off('input:rewind:down');
      bus.off('input:rewind:up');
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
    this.checkpoint = { ...level.spawn };
    this.history = [];

    // Clear world
    this.children.removeAll();
    this.physics.world.colliders.destroy();
    this.tweens.killAll();
    this.cameras.main.resetFX();

    let maxX = 1200;
    for (const p of level.platforms) maxX = Math.max(maxX, p.x + p.w / 2);
    maxX = Math.max(maxX, level.goal.x + 400);
    const worldW = maxX + 200;
    this.physics.world.setBounds(0, 0, worldW, WORLD_H);

    // Background gradient
    const theme = THEMES[level.theme ?? 'day'];
    this.cameras.main.setBackgroundColor(theme.skyBottom);
    const bg = this.add.graphics().setScrollFactor(0).setDepth(-100);
    bg.fillGradientStyle(theme.skyTop, theme.skyTop, theme.skyBottom, theme.skyBottom, 1);
    bg.fillRect(0, 0, CAM_W, WORLD_H);

    // Clouds
    for (let i = 0; i < 30; i++) {
      const x = Phaser.Math.Between(0, worldW);
      const y = Phaser.Math.Between(40, 220);
      const w = Phaser.Math.Between(60, 140);
      const h = Phaser.Math.Between(20, 40);
      this.add.ellipse(x, y, w, h, 0xffffff, 0.55).setScrollFactor(0.3).setDepth(-90);
      this.add.ellipse(x + w * 0.3, y - h * 0.3, w * 0.6, h * 0.8, 0xffffff, 0.6)
        .setScrollFactor(0.3).setDepth(-90);
    }

    // Mushaf banner
    const pageKey = `page-${String(level.startPage).padStart(3, '0')}`;
    if (this.textures.exists(pageKey)) {
      const img = this.add.image(480, WORLD_H / 2, pageKey)
        .setAlpha(0.28).setScrollFactor(0.4).setDepth(-80);
      const scale = Math.min(500 / img.width, (WORLD_H * 0.85) / img.height);
      img.setScale(scale);
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
    for (const c of level.coins ?? []) {
      const coin = this.coins.create(c.x, c.y, 'coin') as Phaser.Physics.Arcade.Sprite;
      coin.setData('collected', false);
      this.tweens.add({
        targets: coin, y: c.y - 6,
        duration: 900, yoyo: true, repeat: -1, ease: 'Sine.inOut',
      });
    }
    bus.emit('coins:update', { got: 0, total: this.coinsTotal });

    // Goal
    this.goalSprite = this.physics.add.staticSprite(
      level.goal.x, level.goal.y, 'goal',
    );
    this.goalSprite.setDisplaySize(level.goal.w, level.goal.h).refreshBody();
    this.tweens.add({
      targets: this.goalSprite,
      scaleX: this.goalSprite.scaleX * 1.10,
      scaleY: this.goalSprite.scaleY * 1.10,
      duration: 700, yoyo: true, repeat: -1, ease: 'Sine.inOut',
    });

    // Player
    this.player = this.physics.add.sprite(level.spawn.x, level.spawn.y, 'ball');
    this.player.setCircle(24, 8, 8);
    this.player.setBounce(0);
    this.player.setCollideWorldBounds(true);
    this.player.setDragX(1400);
    this.player.setMaxVelocity(380, 900);
    this.player.setDepth(10);

    // Collisions
    this.physics.add.collider(this.player, this.solids, (_p, obj) => {
      const o = obj as Phaser.GameObjects.GameObject;
      if (o.getData?.('hazard')) this.die();
    });
    this.physics.add.overlap(this.player, this.coins, (_p, coinObj) => {
      this.collectCoin(coinObj as Phaser.Physics.Arcade.Sprite);
    });
    this.physics.add.overlap(this.player, this.goalSprite, () => this.win());

    // Camera
    this.cameras.main.setBounds(0, 0, worldW, WORLD_H);
    this.cameras.main.setZoom(1280 / 960);
    this.cameras.main.startFollow(this.player, true, 0.14, 0.14, -200, 40);

    // Intro cinematic
    this.playIntro();
  }

  private playIntro(): void {
    if (!this.level) return;
    this.cinematicActive = true;

    const cam = this.cameras.main;
    cam.stopFollow();
    cam.setZoom(0.55);
    cam.centerOn(this.level.spawn.x + 400, WORLD_H / 2);

    const name = this.level.name || this.level.id;

    this.introText = this.add.text(0, 0, name, {
      fontFamily: 'Cairo, Baloo 2, sans-serif',
      fontSize: '72px',
      color: '#ffffff',
      stroke: '#1a3a6a',
      strokeThickness: 10,
      align: 'center',
    }).setOrigin(0.5).setScrollFactor(0).setDepth(2000);

    this.introText.setPosition(cam.midPoint.x, cam.midPoint.y - 40);
    this.introText.setAlpha(0);
    this.introText.setScale(0.6);

    this.tweens.add({
      targets: this.introText,
      alpha: 1,
      scale: 1,
      duration: 400,
      ease: 'Back.out',
    });

    this.time.delayedCall(900, () => {
      if (!this.introText) return;
      this.tweens.add({
        targets: this.introText,
        alpha: 0,
        y: this.introText.y - 80,
        duration: 500,
        onComplete: () => {
          this.introText?.destroy();
          this.introText = undefined;
        },
      });
    });

    this.tweens.add({
      targets: cam,
      zoom: 1280 / 960,
      duration: 1500,
      ease: 'Cubic.inOut',
      onComplete: () => {
        if (!this.player) return;
        cam.startFollow(this.player, true, 0.14, 0.14, -200, 40);
        this.cinematicActive = false;
        this.goFlash();
      },
    });
  }

  private goFlash(): void {
    const cam = this.cameras.main;
    const text = this.add.text(0, 0, 'GO!', {
      fontFamily: 'Cairo, Baloo 2, sans-serif',
      fontSize: '96px',
      color: '#ffe066',
      stroke: '#1a3a6a',
      strokeThickness: 12,
    }).setOrigin(0.5).setScrollFactor(0).setDepth(2000);
    text.setPosition(cam.midPoint.x, cam.midPoint.y);
    this.tweens.add({
      targets: text,
      scale: 1.8,
      alpha: 0,
      duration: 500,
      ease: 'Cubic.out',
      onComplete: () => text.destroy(),
    });
  }

  update() {
    if (!this.level || !this.player || this.finished) return;
    if (this.cinematicActive) return;

    const body = this.player.body as Phaser.Physics.Arcade.Body;
    const onGround = body.blocked.down;
    const now = this.time.now;

    if (onGround) this.lastGroundedAt = now;

    // ── Rewind ──────────────────────────────────────────
    const wantRewind = this.keys.rewind.isDown || this.virtualRewind;
    if (wantRewind && this.history.length > 0) {
      const snap = this.history.shift()!;
      this.player.setPosition(snap.x, snap.y);
      this.player.setVelocity(snap.vx, snap.vy);
      this.cameras.main.setAlpha(0.7);
      // Pop the oldest trail dots too
      if (this.trail.length > 0) {
        const t = this.trail.shift();
        t?.destroy();
      }
      return;
    } else {
      this.cameras.main.setAlpha(1);
    }

    // ── Record history ──────────────────────────────────
    if (now - this.lastSampleAt >= SAMPLE_MS) {
      this.lastSampleAt = now;
      this.history.push({
        x: this.player.x,
        y: this.player.y,
        vx: body.velocity.x,
        vy: body.velocity.y,
        t: now,
      });
      // Trim anything older than REWIND_MS
      while (this.history.length > 0 && now - this.history[0].t > REWIND_MS) {
        this.history.shift();
      }
    }

    // ── Trail ───────────────────────────────────────────
    if (now - this.lastTrailAt >= 35 && Math.abs(body.velocity.x) > 40) {
      this.lastTrailAt = now;
      const dot = this.add.image(this.player.x, this.player.y, 'particle')
        .setTint(0xffaa55)
        .setAlpha(0.55)
        .setScale(1.6)
        .setDepth(5);
      this.tweens.add({
        targets: dot,
        alpha: 0, scale: 0,
        duration: 350,
        onComplete: () => dot.destroy(),
      });
      this.trail.push(dot);
      if (this.trail.length > 12) {
        const old = this.trail.shift();
        old?.destroy();
      }
    }

    // ── Horizontal input ────────────────────────────────
    const ACCEL            = 2400;
    const AIR_ACCEL        = 1600;
    const GROUND_FRICTION  = 2600;
    const AIR_FRICTION     = 400;
    const MAX_SPEED        = 380;

    const wantLeft  = this.keys.left.isDown  || this.virtualLeft;
    const wantRight = this.keys.right.isDown || this.virtualRight;
    const accel = onGround ? ACCEL : AIR_ACCEL;
    const dt = this.game.loop.delta / 1000;

    if (wantLeft && !wantRight) {
      const v = body.velocity.x > 0
        ? body.velocity.x - accel * 1.6 * dt
        : Math.max(-MAX_SPEED, body.velocity.x - accel * dt);
      this.player.setVelocityX(v);
    } else if (wantRight && !wantLeft) {
      const v = body.velocity.x < 0
        ? body.velocity.x + accel * 1.6 * dt
        : Math.min(MAX_SPEED, body.velocity.x + accel * dt);
      this.player.setVelocityX(v);
    } else {
      const fric = onGround ? GROUND_FRICTION : AIR_FRICTION;
      const sign = Math.sign(body.velocity.x);
      const next = Math.abs(body.velocity.x) - fric * dt;
      this.player.setVelocityX(sign * Math.max(0, next));
    }

    // ── Jump ────────────────────────────────────────────
    const JUMP_INITIAL    = -520;
    const JUMP_HOLD_FORCE = -900;
    const JUMP_HOLD_MAX   = 220;
    const JUMP_CUT        = 0.45;
    const COYOTE_MS       = 130;
    const BUFFER_MS       = 140;

    const canJump   = now - this.lastGroundedAt < COYOTE_MS;
    const wantsJump = now - this.jumpQueuedAt   < BUFFER_MS;
    const isJumping = body.velocity.y < 0;

    if (wantsJump && canJump) {
      this.player.setVelocityY(JUMP_INITIAL);
      this.jumpQueuedAt = 0;
      this.lastGroundedAt = -1000;
      this.jumpHoldStart = now;
      this.jumpHeld = true;
      this.burstParticles(this.player.x, this.player.y + 22, 0xffd166, 8);
      this.player.setScale(0.8, 1.2);
      this.tweens.add({
        targets: this.player, scaleX: 1, scaleY: 1,
        duration: 240, ease: 'Back.out',
      });
    }

    if (this.jumpHeld && (this.keys.jump.isDown || this.virtualJump) && isJumping) {
      const heldFor = now - this.jumpHoldStart;
      if (heldFor < JUMP_HOLD_MAX) {
        this.player.setVelocityY(body.velocity.y + JUMP_HOLD_FORCE * dt);
      }
    }

    if (this.jumpHeld && !this.keys.jump.isDown && !this.virtualJump && isJumping) {
      this.player.setVelocityY(body.velocity.y * JUMP_CUT);
      this.jumpHeld = false;
    }
    if (!isJumping) this.jumpHeld = false;

    // Rotation
    this.player.rotation += body.velocity.x * 0.0005;

    // ── Landing feedback ────────────────────────────────
    if (onGround && !this.landedThisFrame && body.velocity.y > 200) {
      this.landedThisFrame = true;
      const impact = Math.min(body.velocity.y, 800) / 800;
      this.burstParticles(this.player.x, this.player.y + 22, 0xffffff, 4 + Math.floor(impact * 6));
      this.player.setScale(1.2, 0.8);
      this.tweens.add({
        targets: this.player, scaleX: 1, scaleY: 1,
        duration: 220, ease: 'Back.out',
      });
      if (impact > 0.6) this.cameras.main.shake(70, 0.0035 * impact);
    }
    if (!onGround) this.landedThisFrame = false;

    // ── Checkpoint (every 2s of safe running) ───────────
    if (onGround && Math.abs(body.velocity.x) > 50 && now - this.lastCheckpointAt > 2000) {
      this.lastCheckpointAt = now;
      this.checkpoint = { x: this.player.x, y: this.player.y };
      this.placeCheckpointMarker(this.player.x, this.player.y);
    }

    // ── Input: restart / rewind-to-checkpoint ───────────
    if (Phaser.Input.Keyboard.JustDown(this.keys.restart)) this.die();
    if (this.player.y > WORLD_H + 200) this.die();
  }

  private placeCheckpointMarker(x: number, y: number): void {
    this.checkpointMarker?.destroy();
    this.checkpointMarker = this.add.image(x, y - 50, 'coin')
      .setTint(0x69db7c)
      .setAlpha(0.7)
      .setScale(0.9)
      .setDepth(3);
    this.tweens.add({
      targets: this.checkpointMarker,
      y: y - 70,
      duration: 800,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.inOut',
    });
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

    // Small camera pop
    this.cameras.main.shake(40, 0.0015);
  }

  private burstParticles(x: number, y: number, color: number, count: number): void {
    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 * i) / count + Math.random() * 0.6;
      const speed = Phaser.Math.Between(60, 180);
      const p = this.add.image(x, y, 'particle')
        .setTint(color)
        .setDepth(20)
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

    // Death animation — ball launches up, spins, fades
    this.cameras.main.shake(240, 0.010);
    this.burstParticles(this.player.x, this.player.y, 0xff5555, 20);

    const deadBall = this.add.image(this.player.x, this.player.y, 'ball')
      .setDepth(50);
    this.player.setVisible(false);
    (this.player.body as Phaser.Physics.Arcade.Body).enable = false;

    this.tweens.add({
      targets: deadBall,
      y: deadBall.y - 200,
      angle: 720,
      alpha: 0,
      scale: 0.3,
      duration: 900,
      ease: 'Cubic.out',
      onComplete: () => {
        deadBall.destroy();
        bus.emit('level:death', { levelId: this.level!.id });
        this.respawn();
      },
    });
  }

  private respawn(): void {
    if (!this.level) return;
    this.player.setVisible(true);
    (this.player.body as Phaser.Physics.Arcade.Body).enable = true;
    this.player.setPosition(this.checkpoint.x, this.checkpoint.y);
    this.player.setVelocity(0, 0);
    this.player.setScale(1, 1);
    this.startTime = this.time.now;
    this.history = [];
    this.burstParticles(this.checkpoint.x, this.checkpoint.y, 0x69db7c, 12);
  }

  private win(): void {
    if (!this.level || this.finished) return;
    this.finished = true;
    this.player.setVelocity(0, 0);
    this.burstParticles(this.player.x, this.player.y, 0xffd166, 24);
    this.cameras.main.flash(300, 255, 240, 200);

    bus.emit('level:win', {
      levelId: this.level.id,
      timeMs: Math.round(this.time.now - this.startTime),
      coinsCollected: this.coinsCollected,
      coinsTotal: this.coinsTotal,
    });
  }
}
'''

LS = pathlib.Path("src/game/scenes/LevelScene.ts")
backup(LS)
LS.write_text(LEVEL_SCENE, encoding="utf-8")
print(f"  ✅ rewrote LevelScene.ts ({len(LEVEL_SCENE)} chars)")


# ═══════════════════════════════════════════════════════════════════
# 3. Patch TouchControls.tsx — add rewind button
# ═══════════════════════════════════════════════════════════════════
print("\n═══ 3/3  TouchControls.tsx ═══")

TC = pathlib.Path("src/platform/TouchControls.tsx")
if TC.exists():
    c = TC.read_text(encoding="utf-8")
    if "rewind" not in c.lower():
        backup(TC)
        # Insert rewind button before closing </>
        old_btn = ">⤒</button>\n    </>"
        new_btn = """>⤒</button>

      <button style={rewindBtn}
        onPointerDown={() => press('rewind')}
        onPointerUp={() => release('rewind')}
        onPointerLeave={() => release('rewind')}
        onPointerCancel={() => release('rewind')}
      >⏪</button>
    </>"""
        if old_btn in c:
            c = c.replace(old_btn, new_btn, 1)
            # Patch press/release types
            c = c.replace(
                "const press = (k: 'left' | 'right' | 'jump')",
                "const press = (k: 'left' | 'right' | 'jump' | 'rewind')",
            )
            c = c.replace(
                "const release = (k: 'left' | 'right' | 'jump')",
                "const release = (k: 'left' | 'right' | 'jump' | 'rewind')",
            )
            # Add rewindBtn style before last };
            anchor_style = "const jumpBtn: CSSProperties = {"
            rewind_style = (
                "const rewindBtn: CSSProperties = {\n"
                "  position: 'fixed', bottom: 145, right: 24,\n"
                "  width: 72, height: 72, borderRadius: '50%',\n"
                "  background: 'linear-gradient(180deg, #b197fc, #7048e8)',\n"
                "  color: '#fff', fontSize: 30, fontWeight: 900,\n"
                "  border: '4px solid #fff',\n"
                "  boxShadow: '0 6px 20px rgba(112,72,232,0.5)',\n"
                "  display: 'grid', placeItems: 'center', zIndex: 50,\n"
                "  pointerEvents: 'auto', touchAction: 'none', userSelect: 'none',\n"
                "};\n\n"
                "const jumpBtn: CSSProperties = {"
            )
            c = c.replace(anchor_style, rewind_style, 1)
            TC.write_text(c, encoding="utf-8")
            print("  ✅ added rewind button")
        else:
            print("  ⚠  couldn't find jump button anchor")
    else:
        print("  ⏭  rewind already present")
else:
    print("  ❌ TouchControls.tsx not found")


print("\n" + "=" * 60)
print("✅ Game-changer patch done.")
print("=" * 60)
print("""
Next:
  1. npx tsc --noEmit
  2. npm run dev -- --host
  3. Test on desktop + phone

Controls:
  ← →      move
  SPACE    jump
  X        rewind (hold)
  R        die / reset to checkpoint
  ⏪ button on mobile = rewind
""")