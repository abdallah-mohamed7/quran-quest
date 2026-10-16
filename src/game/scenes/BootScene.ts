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
