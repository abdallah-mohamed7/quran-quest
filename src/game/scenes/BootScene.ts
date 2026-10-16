import Phaser from 'phaser';
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

  // Platform — rounded top corners, soft edges, no outline
  private makePlatform() {
    const W = 96, H = 44;
    const r = 10;   // corner radius

    const g = this.add.graphics();

    // ── Dirt body with rounded top ────────────────────
    g.fillStyle(0x9b6a3b, 1);
    g.fillRoundedRect(0, 12, W, H - 12, {
      tl: r, tr: r, bl: 0, br: 0,
    });

    // ── Bottom shade ──────────────────────────────────
    g.fillStyle(0x7a5228, 1);
    g.fillRoundedRect(0, H - 10, W, 10, {
      tl: 0, tr: 0, bl: r, br: r,
    });

    // ── Grass cap (rounded top) ───────────────────────
    g.fillStyle(0x6cc24a, 1);
    g.fillRoundedRect(0, 0, W, 18, {
      tl: r, tr: r, bl: 0, br: 0,
    });

    // ── Grass highlight strip ─────────────────────────
    g.fillStyle(0x8ee06b, 1);
    g.fillRoundedRect(0, 0, W, 6, {
      tl: r, tr: r, bl: 0, br: 0,
    });

    // ── Grass tufts ───────────────────────────────────
    g.fillStyle(0x5cb03c, 1);
    for (let x = 6; x < W - 6; x += 14) {
      g.fillTriangle(x, 2, x + 4, -3, x + 8, 2);
    }

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
