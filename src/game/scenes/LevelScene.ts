import Phaser from 'phaser';
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

    const cam = this.cameras.main;
    cam.setBackgroundColor(theme.skyBottom);
    const bg = this.add.graphics().setScrollFactor(0).setDepth(-100);
    bg.fillGradientStyle(theme.skyTop, theme.skyTop, theme.skyBottom, theme.skyBottom, 1);
    bg.fillRect(0, 0, 1280, WORLD_H);

    // Parallax hills
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

    // Decorations
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
    this.player.setCircle(40, 8, 8);
    this.player.setBounce(0);
    this.player.setCollideWorldBounds(true);
    this.player.setDragX(1800);
    this.player.setMaxVelocity(420, 1000);
    this.player.setDepth(10);
    this.player.setScale(0.62);

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
