// src/game/scenes/BootScene.ts
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
