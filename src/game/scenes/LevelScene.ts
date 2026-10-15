// src/game/scenes/LevelScene.ts
import Phaser from 'phaser';
import { bus, state } from '../bus';
import type { LevelDef, Theme } from '../types';

const WORLD_H = 540;
const CAM_W = 960;

const THEMES: Record<Theme, { skyTop: number; skyBottom: number; platform: number }> = {
  day:    { skyTop: 0x4aa8ff, skyBottom: 0xc8e8ff, platform: 0x54cc4a },
  sunset: { skyTop: 0xff8866, skyBottom: 0xffd8a0, platform: 0xff8844 },
  forest: { skyTop: 0x6ac8a8, skyBottom: 0xd8f0e8, platform: 0x4eb85a },
  candy:  { skyTop: 0xff8ac8, skyBottom: 0xffe0f0, platform: 0xd060d0 },
  ocean:  { skyTop: 0x4ac8ff, skyBottom: 0xd0f0ff, platform: 0x4a90e0 },
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
      this.jumpQueuedAt = this.time.now;
    });

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
      s.setDisplaySize(p.w, Math.max(p.h, 16)).refreshBody();
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
    this.cameras.main.setZoom(1);

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
