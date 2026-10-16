"""Rounded corners on platforms — softer, modern look."""

import pathlib
import shutil
import subprocess
import sys

PROJECT = pathlib.Path(r"C:\Users\amaha\quran-quest")
BS = PROJECT / "src" / "game" / "scenes" / "BootScene.ts"

if not BS.exists():
    print("X  BootScene.ts not found")
    sys.exit(1)

shutil.copy2(BS, BS.with_suffix(".ts.bak_round"))

new_makePlatform = '''  // Platform — rounded top corners, soft edges, no outline
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
  }'''

c = BS.read_text(encoding="utf-8")

# Find and replace makePlatform (handles multiple variants)
import re
pattern = re.compile(
    r"  // Platform[^\n]*\n  private makePlatform\(\) \{[\s\S]*?\n  \}",
    re.MULTILINE,
)
before = c
c = pattern.sub(new_makePlatform, c, count=1)

if c == before:
    print("X  makePlatform not found — paste current version")
    sys.exit(1)

BS.write_text(c, encoding="utf-8")
print("OK  makePlatform rewritten with rounded corners")

print("\nBuilding...")
r = subprocess.run("npm run build", shell=True, cwd=str(PROJECT))
if r.returncode != 0:
    print("X  build failed")
    sys.exit(1)

print("\n" + "=" * 55)
print("Done.  Next:  npm run dev")
print("=" * 55)
print("""
Platform is now 96x44 with:
  - Rounded top-left and top-right corners (10px radius)
  - Rounded bottom-left and bottom-right corners
  - No outline
  - 3-layer shading (grass / grass highlight / dirt + bottom shade)
""")