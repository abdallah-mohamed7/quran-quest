"""Switch audio to per-surah + apply flat design visuals."""
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(".").resolve()
if not (ROOT / "package.json").exists():
    print("❌ run from inside quran-quest")
    sys.exit(1)


def backup(p):
    bak = p.with_suffix(p.suffix + ".bak_flat")
    if not bak.exists() and p.exists():
        shutil.copy2(p, bak)


def write(p_str, content):
    p = ROOT / p_str
    backup(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  ✅ {p_str}")


# ══════════════════════════════════════════════════════════
# 1. types.ts — add surah field
# ══════════════════════════════════════════════════════════
write("src/game/types.ts", '''// src/game/types.ts
export type PageAudio = { page: number; file: string };
export type AyahAudio = { surah: number; ayah: number; file: string };

export type Rect = { x: number; y: number; w: number; h: number };

export type Theme = 'day' | 'sunset' | 'forest' | 'candy' | 'ocean';

export type LevelDef = {
  id: string;
  name: string;           // Arabic name of the surah
  theme?: Theme;
  surah: number;          // 105..114
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
''')


# ══════════════════════════════════════════════════════════
# 2. New level JSONs — one surah each
# ══════════════════════════════════════════════════════════
SURAHS = {
    1:  (105, "الفيل",        "day"),
    2:  (106, "قريش",         "day"),
    3:  (107, "الماعون",      "sunset"),
    4:  (108, "الكوثر",       "candy"),
    5:  (109, "الكافرون",     "forest"),
    6:  (110, "النصر",        "ocean"),
    7:  (111, "المسد",        "sunset"),
    8:  (112, "الإخلاص",      "candy"),
    9:  (113, "الفلق",        "forest"),
    10: (114, "الناس",        "day"),
}

# Hand-crafted layouts per level — teaching + play + reward.
# Widening as levels progress.
def make_level(n, surah, name, theme):
    W = 4200 + n * 400   # 4600 → 8200 px wide

    # Intro zone
    plats = [{"x": 500, "y": 520, "w": 900, "h": 40}]
    coins = [
        {"x": 300, "y": 460},
        {"x": 550, "y": 460},
        {"x": 800, "y": 460},
    ]
    x = 950
    y = 520

    # Rhythm: easy → medium → challenge → easy
    rhythm = [
        # (width, gap, dy) — small rise
        (260, 120, -50), (260, 130, 50),
        (240, 140, -80), (240, 140, 80),
        (280, 120, -60), (280, 120, 60),
        (220, 150, -100), (220, 150, 100),
        (300, 120, -40), (300, 120, 40),
    ]

    for i, (w, gap, dy) in enumerate(rhythm):
        nx = x + gap
        ny = max(300, min(520, y + dy))
        h = 40 if ny == 520 else 30
        plats.append({"x": nx + w / 2, "y": ny, "w": w, "h": h})
        coins.append({"x": nx + w / 2, "y": ny - 70})
        if i % 3 == 1:
            coins.append({"x": nx + w / 2 - 60, "y": ny - 100})
            coins.append({"x": nx + w / 2 + 60, "y": ny - 100})
        x = nx + w
        y = ny

    # Hazards appear from level 3 onward, in the gaps
    hazards = []
    if n >= 3:
        hazards.append({"x": 2100, "y": 480, "w": 60, "h": 60})
    if n >= 5:
        hazards.append({"x": 3200, "y": 480, "w": 60, "h": 60})
    if n >= 7:
        hazards.append({"x": 2600, "y": 480, "w": 60, "h": 60})
    if n >= 9:
        hazards.append({"x": 3800, "y": 480, "w": 60, "h": 60})

    # Outro — safe reward zone with the goal
    outro_x = max(x + 400, W - 600)
    plats.append({"x": outro_x, "y": 520, "w": 1200, "h": 40})
    coins.append({"x": outro_x - 300, "y": 460})
    coins.append({"x": outro_x, "y": 460})

    return {
        "id": f"level-{n:03d}",
        "name": name,
        "theme": theme,
        "surah": surah,
        "spawn": {"x": 100, "y": 400},
        "platforms": plats,
        "hazards": hazards,
        "coins": coins,
        "goal": {"x": outro_x + 400, "y": 460, "w": 80, "h": 120},
    }


LEVELS_DIR = ROOT / "src" / "game" / "levels"
for n in range(1, 11):
    surah, name, theme = SURAHS[n]
    lvl = make_level(n, surah, name, theme)
    p = LEVELS_DIR / f"level-{n:03d}.json"
    if p.exists():
        backup(p)
    p.write_text(json.dumps(lvl, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  ✅ level-{n:03d}.json — {name} (surah {surah}, {len(lvl['coins'])} coins)")


# ══════════════════════════════════════════════════════════
# 3. QuranAudio — supports ayah queue
# ══════════════════════════════════════════════════════════
write("src/game/systems/QuranAudio.ts", '''// src/game/systems/QuranAudio.ts
export type Ayah = { surah: number; ayah: number; file: string };

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
    this.el.addEventListener('play',  () => this.dispatchEvent(new Event('play')));
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
    try { await this.el.play(); } catch (e) { console.warn(e); }
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
      this.dispatchEvent(new CustomEvent<Ayah>('ayah', { detail: cur }));
    } catch {
      this.dispatchEvent(new CustomEvent<Ayah>('ayah', { detail: cur }));
    }
  }

  private next(): void {
    if (this.queue.length === 0) return;
    this.index = (this.index + 1) % this.queue.length;  // loop forever
    void this.playCurrent();
  }
}

export const quranAudio = new QuranAudio();
''')


# ══════════════════════════════════════════════════════════
# 4. BootScene — flat kid-friendly textures
# ══════════════════════════════════════════════════════════
write("src/game/scenes/BootScene.ts", '''// src/game/scenes/BootScene.ts
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

  // Red ball WITH EYES — instantly becomes a character.
  private makeBall() {
    const S = 96, c = S / 2;
    const g = this.add.graphics();
    // body
    g.fillStyle(0xff4d4d, 1).fillCircle(c, c, 40);
    // subtle top highlight (still flat-ish)
    g.fillStyle(0xff7070, 1).fillCircle(c - 4, c - 4, 34);
    // eyes — white
    g.fillStyle(0xffffff, 1).fillCircle(c - 13, c - 6, 10);
    g.fillStyle(0xffffff, 1).fillCircle(c + 13, c - 6, 10);
    // pupils — black, looking slightly right
    g.fillStyle(0x1a1a1a, 1).fillCircle(c - 10, c - 6, 5);
    g.fillStyle(0x1a1a1a, 1).fillCircle(c + 16, c - 6, 5);
    // tiny shine
    g.fillStyle(0xffffff, 0.9).fillCircle(c - 12, c - 8, 2);
    g.fillStyle(0xffffff, 0.9).fillCircle(c + 14, c - 8, 2);
    g.generateTexture('ball', S, S);
    g.destroy();
  }

  // Flat platform — pure white, tinted per level. Grass tufts on top.
  private makePlatform() {
    const W = 64, H = 24;
    const g = this.add.graphics();
    // base
    g.fillStyle(0xffffff, 1).fillRoundedRect(0, 6, W, H - 6, 6);
    // grass tufts (slightly bigger triangles on top)
    g.fillStyle(0xffffff, 1);
    for (let x = 2; x < W; x += 10) {
      g.fillTriangle(x, 6, x + 5, 0, x + 10, 6);
    }
    g.generateTexture('platform', W, H);
    g.destroy();
  }

  // Coin — solid gold with sparkle dot
  private makeCoin() {
    const S = 44, c = S / 2;
    const g = this.add.graphics();
    g.fillStyle(0xffc233, 1).fillCircle(c, c, 15);
    g.fillStyle(0xffe066, 1).fillCircle(c - 2, c - 2, 11);
    g.fillStyle(0xfffbc4, 1).fillCircle(c - 4, c - 4, 4);
    g.generateTexture('coin', S, S);
    g.destroy();
  }

  // Hazards — clean red triangles
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

  // Goal — clean concentric portal
  private makeGoal() {
    const W = 90, H = 130, cx = W / 2, cy = H / 2;
    const g = this.add.graphics();
    g.fillStyle(0xffffff, 0.15).fillCircle(cx, cy, 46);
    g.lineStyle(5, 0xffffff, 0.95).strokeCircle(cx, cy, 44);
    g.lineStyle(3, 0x88ddff, 1).strokeCircle(cx, cy, 32);
    g.lineStyle(2, 0xffd166, 1).strokeCircle(cx, cy, 22);
    g.fillStyle(0xffffff, 1).fillCircle(cx, cy, 8);
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
}
''')


# ══════════════════════════════════════════════════════════
# 5. LevelScene — parallax background, no page image
# ══════════════════════════════════════════════════════════
LS = ROOT / "src" / "game" / "scenes" / "LevelScene.ts"
if LS.exists():
    backup(LS)
    c = LS.read_text(encoding="utf-8")

    # Brighten themes with paler skies
    old_themes = '''const THEMES: Record<Theme, { skyTop: number; skyBottom: number; platform: number }> = {
  day:    { skyTop: 0x4aa8ff, skyBottom: 0xc8e8ff, platform: 0x54cc4a },
  sunset: { skyTop: 0xff8866, skyBottom: 0xffd8a0, platform: 0xff8844 },
  forest: { skyTop: 0x6ac8a8, skyBottom: 0xd8f0e8, platform: 0x4eb85a },
  candy:  { skyTop: 0xff8ac8, skyBottom: 0xffe0f0, platform: 0xd060d0 },
  ocean:  { skyTop: 0x4ac8ff, skyBottom: 0xd0f0ff, platform: 0x4a90e0 },
};'''
    new_themes = '''const THEMES: Record<Theme, {
  skyTop: number; skyBottom: number; hill: number; platform: number;
}> = {
  day:    { skyTop: 0x9cd4ff, skyBottom: 0xd8ecff, hill: 0xb8e0c8, platform: 0x54cc4a },
  sunset: { skyTop: 0xffbca0, skyBottom: 0xffe8cc, hill: 0xffcfb0, platform: 0xff8844 },
  forest: { skyTop: 0xb0e0d0, skyBottom: 0xe0f4ec, hill: 0x9cd8c0, platform: 0x4eb85a },
  candy:  { skyTop: 0xffc0e0, skyBottom: 0xfff0fa, hill: 0xffd0ec, platform: 0xd060d0 },
  ocean:  { skyTop: 0x9cd4ff, skyBottom: 0xe0f4ff, hill: 0xb8e0f0, platform: 0x4a90e0 },
};'''
    if old_themes in c:
        c = c.replace(old_themes, new_themes, 1)

    # Remove the page image block (find any version)
    import re
    c = re.sub(
        r"\s*// ── (?:Faint mushaf|Mushaf page)[^\n]*\n(?:[^\n]*\n){0,12}?    \}\n",
        "\n",
        c,
    )
    c = re.sub(
        r"\s*const pageKey[^\n]*\n(?:[^\n]*\n){0,10}?    \}\n",
        "\n",
        c,
    )

    # Add parallax hills after cloud loop
    cloud_anchor = "    // ── Platforms"
    parallax = '''    // ── Parallax hills (three layers of soft rounded triangles) ──
    const hillLayer = (count: number, yBase: number, w: number, h: number, color: number, alpha: number, parallax: number) => {
      for (let i = 0; i < count; i++) {
        const hx = (i * (worldW / count)) + Phaser.Math.Between(-200, 200);
        const hy = yBase + Phaser.Math.Between(-30, 30);
        const g = this.add.graphics().setScrollFactor(parallax).setDepth(-85);
        g.fillStyle(color, alpha);
        g.fillEllipse(hx, hy, w, h * 2);
      }
    };
    hillLayer(8, WORLD_H + 40, 380, 140, theme.hill, 0.55, 0.15);
    hillLayer(6, WORLD_H + 90, 500, 180, theme.hill, 0.75, 0.3);
    hillLayer(5, WORLD_H + 140, 620, 220, theme.hill, 0.95, 0.5);

'''
    if "Parallax hills" not in c:
        c = c.replace(cloud_anchor, parallax + cloud_anchor, 1)

    LS.write_text(c, encoding="utf-8")
    print(f"  ✅ LevelScene.ts — parallax hills, brighter themes")


# ══════════════════════════════════════════════════════════
# 6. GameScreen — build ayah queue from surah number
# ══════════════════════════════════════════════════════════
GS = ROOT / "src" / "platform" / "GameScreen.tsx"
if GS.exists():
    backup(GS)
    c = GS.read_text(encoding="utf-8")

    # Replace the audio queue building block
    old_queue = """    const queue: PageAudio[] = [];
    for (let p = level.startPage; p <= level.endPage; p++) {
      queue.push({
        page: p,
        file: `quran/audio/pages/${String(p).padStart(3, '0')}.mp3`,
      });
    }
    quranAudio.load(queue);"""
    new_queue = """    // Build an ayah queue for this surah.
    // Ayah counts for surahs 105-114 (well-known, fixed).
    const AYAH_COUNTS: Record<number, number> = {
      105: 5, 106: 4, 107: 7, 108: 3, 109: 6,
      110: 3, 111: 5, 112: 4, 113: 5, 114: 6,
    };
    const count = AYAH_COUNTS[level.surah] ?? 1;
    const queue = [];
    for (let a = 1; a <= count; a++) {
      queue.push({
        surah: level.surah,
        ayah: a,
        file: `quran/audio/surahs/${String(level.surah).padStart(3, '0')}/${String(a).padStart(3, '0')}.mp3`,
      });
    }
    quranAudio.load(queue);"""
    if old_queue in c:
        c = c.replace(old_queue, new_queue, 1)

    # Update imports
    c = c.replace(
        "import type { LevelDef, LevelResult, PageAudio, Theme } from '../game/types';",
        "import type { LevelDef, LevelResult, Theme } from '../game/types';\n"
        "import type { Ayah } from '../game/systems/QuranAudio';",
    )

    # Replace page state with ayah
    c = c.replace(
        "const [currentPage, setCurrentPage] = useState<PageAudio | null>(null);",
        "const [currentAyah, setCurrentAyah] = useState<Ayah | null>(null);",
    )
    c = c.replace(
        "const onPage = (e: Event) =>\n      setCurrentPage((e as CustomEvent<PageAudio>).detail);",
        "const onAyah = (e: Event) =>\n      setCurrentAyah((e as CustomEvent<Ayah>).detail);",
    )
    c = c.replace("quranAudio.addEventListener('page', onPage);",
                  "quranAudio.addEventListener('ayah', onAyah);")
    c = c.replace("quranAudio.removeEventListener('page', onPage);",
                  "quranAudio.removeEventListener('ayah', onAyah);")

    # Replace page HUD with ayah HUD
    old_hud = """{currentPage && (
          <div style={{ ...pill, top: 14, left: 14 }}>
            📖 <span className="ar" style={{ fontWeight: 800 }}>صفحة {currentPage.page}</span>
          </div>
        )}"""
    new_hud = """{currentAyah && (
          <div style={{ ...pill, top: 14, left: 14 }}>
            📖 <span className="ar" style={{ fontWeight: 800 }}>
              {currentAyah.surah}:{currentAyah.ayah}
            </span>
          </div>
        )}"""
    if old_hud in c:
        c = c.replace(old_hud, new_hud, 1)

    GS.write_text(c, encoding="utf-8")
    print(f"  ✅ GameScreen.tsx — surah-based audio queue")


print("\n" + "=" * 55)
print("✅ Done.")
print("=" * 55)
print("""
Next:
  1. Delete the old page audio:
       Remove-Item -Recurse -Force public\\quran\\audio\\pages
  2. npm run dev
  3. Check the game works with the new flat look
  4. Rebuild the APK:
       python scripts/build_apk.py
""")