"""Elite kid-friendly platformer level generator.
Chunk-based: hand-crafted moments stitched together procedurally."""
import json
import pathlib
import random

OUT = pathlib.Path("src/game/levels")
OUT.mkdir(parents=True, exist_ok=True)

# ── Level metadata ─────────────────────────────────────
# (page, arabic surah, transliteration)
# (page, arabic names, latin names)
LEVELS = [
    (604, "الإخلاص · الفلق · الناس",
          ),
    (603, "الكوثر · الكافرون · النصر · المسد",
        ),
    (602, "قريش · الماعون · الكوثر",
          ),
    (601, "العصر · الهمزة · الفيل",
          ),
    (600, "العاديات · القارعة · التكاثر",
          ),
    (599, "البينة · الزلزلة · العاديات",
          ),
    (598, "العلق · القدر · البينة",
          ),
    (597, "الشرح · التين · العلق",
          ),
    (596, "الليل · الضحى · الشرح",
          ),
    (595, "الشمس · الليل",
          ),
]

THEMES = ["day", "sunset", "forest", "candy", "ocean",
          "day", "sunset", "forest", "candy", "ocean"]

# 0 = gentle intro, 5 = hardest
DIFFICULTY = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5]

# Longer levels as you progress
WIDTHS = [7000, 7800, 8500, 9200, 10000, 10800, 11500, 12300, 13000, 14000]


# ── Chunk library ──────────────────────────────────────
# Each chunk function returns:
#   platforms, hazards, coins, width, end_y

def ch_flat(x, y, rng, d):
    """Safe ground with a line of coins."""
    w = rng.choice([500, 600, 700])
    return {
        "platforms": [{"x": x + w/2, "y": y, "w": w, "h": 40}],
        "hazards": [],
        "coins": [{"x": x + w*0.3, "y": y - 60},
                  {"x": x + w*0.6, "y": y - 60}],
        "width": w, "end_y": y,
    }


def ch_stair_up(x, y, rng, d):
    """3 ascending platforms."""
    plats, coins = [], []
    cx = x
    cy = y
    for _ in range(3):
        cx += 140
        cy -= 60
        plats.append({"x": cx + 100, "y": cy, "w": 200, "h": 30})
        coins.append({"x": cx + 100, "y": cy - 60})
        cx += 200
    return {"platforms": plats, "hazards": [], "coins": coins,
            "width": cx - x + 140, "end_y": cy}


def ch_stair_down(x, y, rng, d):
    """3 descending platforms."""
    plats, coins = [], []
    cx = x
    cy = y
    for _ in range(3):
        cx += 140
        cy += 60
        plats.append({"x": cx + 100, "y": cy, "w": 200, "h": 30})
        coins.append({"x": cx + 100, "y": cy - 60})
        cx += 200
    return {"platforms": plats, "hazards": [], "coins": coins,
            "width": cx - x + 140, "end_y": cy}


def ch_small_gap(x, y, rng, d):
    """One medium gap with a coin arc over it."""
    w1, gap, w2 = 240, 140, 240
    plats = [
        {"x": x + w1/2, "y": y, "w": w1, "h": 40},
        {"x": x + w1 + gap + w2/2, "y": y, "w": w2, "h": 40},
    ]
    arc_y = y - 120
    coins = [
        {"x": x + w1 + gap*0.25, "y": arc_y + 30},
        {"x": x + w1 + gap*0.5,  "y": arc_y},
        {"x": x + w1 + gap*0.75, "y": arc_y + 30},
    ]
    return {"platforms": plats, "hazards": [], "coins": coins,
            "width": w1 + gap + w2, "end_y": y}


def ch_big_gap(x, y, rng, d):
    """One long gap. Requires a good running jump."""
    if d < 2:
        return ch_small_gap(x, y, rng, d)
    w1, gap, w2 = 260, 220, 260
    plats = [
        {"x": x + w1/2, "y": y, "w": w1, "h": 40},
        {"x": x + w1 + gap + w2/2, "y": y, "w": w2, "h": 40},
    ]
    arc_y = y - 150
    coins = [
        {"x": x + w1 + gap*0.2, "y": arc_y + 40},
        {"x": x + w1 + gap*0.5, "y": arc_y},
        {"x": x + w1 + gap*0.8, "y": arc_y + 40},
    ]
    return {"platforms": plats, "hazards": [], "coins": coins,
            "width": w1 + gap + w2, "end_y": y}


def ch_pit_hazard(x, y, rng, d):
    """Gap with spikes at the bottom — must clear it or die."""
    if d < 1:
        return ch_small_gap(x, y, rng, d)
    w1, gap, w2 = 260, 180, 260
    plats = [
        {"x": x + w1/2, "y": y, "w": w1, "h": 40},
        {"x": x + w1 + gap + w2/2, "y": y, "w": w2, "h": 40},
    ]
    hazards = [{"x": x + w1 + gap/2, "y": 510, "w": gap - 40, "h": 60}]
    coins = [
        {"x": x + w1 + gap*0.5, "y": y - 140},
    ]
    return {"platforms": plats, "hazards": hazards, "coins": coins,
            "width": w1 + gap + w2, "end_y": y}


def ch_hazard_run(x, y, rng, d):
    """Wide ground with spikes on it — jump over them."""
    if d < 2:
        return ch_flat(x, y, rng, d)
    w = rng.choice([500, 600])
    spikes = rng.randint(1, 2)
    hazards = []
    coins = []
    for i in range(spikes):
        sx = x + w * (0.35 + i * 0.3)
        hazards.append({"x": sx, "y": y - 30, "w": 40, "h": 60})
        coins.append({"x": sx, "y": y - 140})
    return {
        "platforms": [{"x": x + w/2, "y": y, "w": w, "h": 40}],
        "hazards": hazards, "coins": coins,
        "width": w, "end_y": y,
    }


def ch_islands(x, y, rng, d):
    """3 small floating platforms with gaps — rhythm section."""
    if d < 1:
        return ch_flat(x, y, rng, d)
    plats, coins = [], []
    cx = x
    for i in range(3):
        w = 140
        gap = 100
        # Alternate heights slightly
        cy = y - (30 if i % 2 == 0 else 60)
        plats.append({"x": cx + w/2, "y": cy, "w": w, "h": 30})
        coins.append({"x": cx + w/2, "y": cy - 60})
        cx += w + gap
    return {"platforms": plats, "hazards": [], "coins": coins,
            "width": cx - x, "end_y": y - 30}


def ch_double_gap(x, y, rng, d):
    """Two quick gaps — tests rhythm."""
    if d < 2:
        return ch_small_gap(x, y, rng, d)
    plats, coins = [], []
    cx = x
    for _ in range(2):
        w = 200
        gap = 140
        plats.append({"x": cx + w/2, "y": y, "w": w, "h": 40})
        coins.append({"x": cx + w/2, "y": y - 60})
        cx += w + gap
    plats.append({"x": cx + 100, "y": y, "w": 200, "h": 40})
    return {"platforms": plats, "hazards": [], "coins": coins,
            "width": cx + 200 - x, "end_y": y}


def ch_coin_bonus(x, y, rng, d):
    """A high platform full of coins — rewards the brave."""
    plats = [
        {"x": x + 150, "y": y - 180, "w": 200, "h": 30},
        {"x": x + 450, "y": y, "w": 300, "h": 40},
    ]
    coins = [
        {"x": x + 100, "y": y - 240},
        {"x": x + 150, "y": y - 240},
        {"x": x + 200, "y": y - 240},
        {"x": x + 150, "y": y - 280},
    ]
    return {"platforms": plats, "hazards": [], "coins": coins,
            "width": 750, "end_y": y}


# Chunk pool per difficulty
CHUNKS_BY_DIFF = {
    0: [ch_flat, ch_flat, ch_flat, ch_small_gap, ch_stair_up],
    1: [ch_flat, ch_small_gap, ch_stair_up, ch_stair_down, ch_coin_bonus],
    2: [ch_flat, ch_small_gap, ch_pit_hazard, ch_islands, ch_stair_up, ch_coin_bonus],
    3: [ch_small_gap, ch_pit_hazard, ch_hazard_run, ch_islands, ch_stair_up, ch_double_gap, ch_coin_bonus],
    4: [ch_small_gap, ch_big_gap, ch_pit_hazard, ch_hazard_run, ch_islands, ch_double_gap, ch_coin_bonus],
    5: [ch_big_gap, ch_pit_hazard, ch_hazard_run, ch_double_gap, ch_islands, ch_hazard_run, ch_coin_bonus],
}


def generate_level(idx, page, arabic, translit, theme, width, difficulty, seed):
    rng = random.Random(seed)

    platforms, hazards, coins = [], [], []

    # ── Safe intro (always the same, teaches the controls) ──
    platforms.append({"x": 500, "y": 520, "w": 1000, "h": 40})
    coins += [
        {"x": 300, "y": 460},
        {"x": 500, "y": 460},
        {"x": 700, "y": 460},
    ]
    x = 1000
    y = 520

    # ── Body: chunks until we reach target width ───────────
    pool = CHUNKS_BY_DIFF[difficulty]
    last_chunk = None
    while x < width - 1400:
        # avoid the same chunk twice in a row for variety
        choices = [c for c in pool if c is not last_chunk]
        chunk_fn = rng.choice(choices)
        result = chunk_fn(x, y, rng, difficulty)

        platforms.extend(result["platforms"])
        hazards.extend(result["hazards"])
        coins.extend(result["coins"])

        x += result["width"]
        y = result["end_y"]
        y = max(300, min(520, y))
        last_chunk = chunk_fn

    # ── Safe outro: wide ground + goal ─────────────────────
    platforms.append({"x": x + 500, "y": 520, "w": 1200, "h": 40})
    coins += [
        {"x": x + 200, "y": 460},
        {"x": x + 500, "y": 460},
        {"x": x + 800, "y": 460},
    ]
    goal = {"x": x + 1000, "y": 460, "w": 80, "h": 120}

    return {
        "id": f"level-{idx:03d}",
        "name": f"{translit} — {arabic}",
        "theme": theme,
        "startPage": page,
        "endPage": page,
        "spawn": {"x": 100, "y": 400},
        "platforms": platforms,
        "hazards": hazards,
        "coins": coins,
        "goal": goal,
    }


for i in range(10):
    idx = i + 1
    page, arabic, translit = LEVELS[i]
    lvl = generate_level(
        idx, page, arabic, translit,
        theme=THEMES[i],
        width=WIDTHS[i],
        difficulty=DIFFICULTY[i],
        seed=idx * 7919,
    )
    path = OUT / f"{lvl['id']}.json"
    path.write_text(json.dumps(lvl, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  {path.name}: {len(lvl['platforms'])} plats, "
          f"{len(lvl['hazards'])} haz, {len(lvl['coins'])} coins, "
          f"page {page}, ~{WIDTHS[i]}px")

print(f"\n✅ Regenerated 10 elite levels in {OUT.resolve()}")