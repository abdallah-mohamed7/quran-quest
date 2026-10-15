"""Add Tailwind CSS v4 + redesign Menu, LevelSelect, GameScreen."""
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(".").resolve()
if not (ROOT / "package.json").exists():
    print("❌ run from inside quran-quest")
    sys.exit(1)


def backup(p: pathlib.Path):
    if p.exists():
        bak = p.with_suffix(p.suffix + ".bak_tw")
        if not bak.exists():
            shutil.copy2(p, bak)
            print(f"  💾 {bak.name}")


# ══════════════════════════════════════════════════════════
# 1. Install Tailwind
# ══════════════════════════════════════════════════════════
print("═══ 1/6  Installing Tailwind ═══")
r = subprocess.run(
    "npm install tailwindcss @tailwindcss/vite",
    shell=True, cwd=str(ROOT),
)
if r.returncode != 0:
    print("⚠  npm install failed — run manually:")
    print("   npm install tailwindcss @tailwindcss/vite")
else:
    print("  ✅ installed")


# ══════════════════════════════════════════════════════════
# 2. vite.config.ts
# ══════════════════════════════════════════════════════════
print("\n═══ 2/6  vite.config.ts ═══")
VC = ROOT / "vite.config.ts"
backup(VC)
VC.write_text('''import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  base: './',
  plugins: [react(), tailwindcss()],
});
''', encoding="utf-8")
print("  ✅ vite.config.ts")


# ══════════════════════════════════════════════════════════
# 3. index.html — add Google Fonts
# ══════════════════════════════════════════════════════════
print("\n═══ 3/6  index.html ═══")
IH = ROOT / "index.html"
if IH.exists():
    backup(IH)
    c = IH.read_text(encoding="utf-8")
    if "fonts.googleapis" not in c:
        c = c.replace(
            "</head>",
            '  <link rel="preconnect" href="https://fonts.googleapis.com" />\n'
            '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n'
            '  <link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;700;800;900&family=Cairo:wght@400;700;900&display=swap" rel="stylesheet" />\n'
            "</head>",
        )
        IH.write_text(c, encoding="utf-8")
        print("  ✅ font links added")


# ══════════════════════════════════════════════════════════
# 4. index.css
# ══════════════════════════════════════════════════════════
print("\n═══ 4/6  index.css ═══")
IC = ROOT / "src" / "index.css"
backup(IC)
IC.write_text('''@import "tailwindcss";

@theme {
  --font-display: "Baloo 2", system-ui, sans-serif;
  --font-arabic: "Cairo", system-ui, sans-serif;

  --animate-float: float 6s ease-in-out infinite;
  --animate-bob: bob 2.4s ease-in-out infinite;
  --animate-twinkle: twinkle 2.5s ease-in-out infinite;
  --animate-pop: pop 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(-14px); }
}
@keyframes bob {
  0%, 100% { transform: translateY(0) rotate(-3deg); }
  50%      { transform: translateY(-8px) rotate(3deg); }
}
@keyframes twinkle {
  0%, 100% { opacity: 0.4; transform: scale(0.9); }
  50%      { opacity: 1; transform: scale(1.15); }
}
@keyframes pop {
  0%   { transform: scale(0.7); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}

html, body, #root {
  height: 100%;
  margin: 0;
  padding: 0;
}

body {
  font-family: var(--font-display);
  background: #a8d8ff;
  color: #1a2a4a;
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
}

button { font-family: inherit; }

canvas {
  display: block;
  outline: none;
  touch-action: none;
}
''', encoding="utf-8")
print("  ✅ index.css")


# ══════════════════════════════════════════════════════════
# 5. Menu.tsx
# ══════════════════════════════════════════════════════════
print("\n═══ 5/6  Menu.tsx ═══")
M = ROOT / "src" / "platform" / "Menu.tsx"
backup(M)
M.write_text('''// src/platform/Menu.tsx
import { progress } from '../game/progress';

export default function Menu({ onStart }: { onStart: () => void }) {
  return (
    <div className="relative h-screen w-full overflow-hidden bg-gradient-to-b from-sky-400 via-sky-200 to-amber-100 flex items-center justify-center">

      {/* Floating clouds */}
      <div className="pointer-events-none absolute top-[12%] left-[8%]  h-12 w-40 rounded-full bg-white/70 blur-[1px] animate-float" />
      <div className="pointer-events-none absolute top-[65%] left-[12%] h-10 w-32 rounded-full bg-white/60 blur-[1px] animate-float [animation-delay:1.5s]" />
      <div className="pointer-events-none absolute top-[22%] right-[10%] h-14 w-48 rounded-full bg-white/70 blur-[1px] animate-float [animation-delay:0.7s]" />
      <div className="pointer-events-none absolute top-[70%] right-[15%] h-10 w-36 rounded-full bg-white/60 blur-[1px] animate-float [animation-delay:2.1s]" />

      {/* Sparkles */}
      {[...Array(8)].map((_, i) => (
        <span
          key={i}
          className="pointer-events-none absolute select-none animate-twinkle"
          style={{
            top: `${8 + (i * 11) % 82}%`,
            left: `${(i * 27) % 92}%`,
            fontSize: 14 + (i % 3) * 8,
            animationDelay: `${i * 0.28}s`,
          }}
        >⭐</span>
      ))}

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center px-6 text-center">

        <div className="text-[8rem] leading-none animate-bob drop-shadow-[0_12px_24px_rgba(239,68,68,0.35)]">
          🎈
        </div>

        <h1 className="font-display text-[clamp(3rem,10vw,6rem)] font-black leading-none tracking-tight mt-3">
          <span className="text-orange-500 drop-shadow-[0_4px_0_rgba(255,255,255,0.95)]">
            Quran
          </span>{' '}
          <span className="text-sky-600 drop-shadow-[0_4px_0_rgba(255,255,255,0.95)]">
            Quest
          </span>
        </h1>

        <p
          dir="rtl"
          className="font-arabic text-2xl md:text-3xl font-bold text-slate-700 mt-3 mb-10"
        >
          ارْكض · اقِف · اسْتَمِع
        </p>

        <button
          onClick={onStart}
          className="
            px-12 py-5 rounded-full
            font-display text-3xl md:text-4xl font-black text-white
            bg-gradient-to-b from-orange-400 to-orange-500
            shadow-[0_8px_0_#c2410c,0_14px_32px_rgba(234,88,12,0.45)]
            active:translate-y-1 active:shadow-[0_3px_0_#c2410c]
            transition-all duration-100
            flex items-center gap-3
          "
        >
          <span className="text-2xl">▶</span>
          <span>Let&apos;s Play!</span>
        </button>

        <p className="mt-10 text-sm text-slate-600 font-medium opacity-80">
          ← → move &nbsp;·&nbsp; SPACE jump &nbsp;·&nbsp; R restart
        </p>

        <button
          onClick={() => {
            if (window.confirm('Reset all stars and progress?')) {
              progress.clear();
              window.location.reload();
            }
          }}
          className="
            mt-5 px-5 py-2 rounded-full
            bg-white/70 border-2 border-white
            text-slate-700 text-sm font-bold
            shadow-sm hover:bg-white/90
            transition-colors
          "
        >
          🔄 Reset progress
        </button>
      </div>
    </div>
  );
}
''', encoding="utf-8")
print("  ✅ Menu.tsx")


# ══════════════════════════════════════════════════════════
# 6. LevelSelect.tsx
# ══════════════════════════════════════════════════════════
print("\n═══ 6/6  LevelSelect.tsx ═══")
LS = ROOT / "src" / "platform" / "LevelSelect.tsx"
backup(LS)
LS.write_text('''// src/platform/LevelSelect.tsx
import levels from '../game/levels';
import { progress } from '../game/progress';

const GRADIENTS = [
  'from-rose-400 to-rose-500',
  'from-orange-400 to-orange-500',
  'from-amber-400 to-amber-500',
  'from-lime-400 to-green-500',
  'from-emerald-400 to-teal-500',
  'from-sky-400 to-blue-500',
  'from-indigo-400 to-indigo-500',
  'from-violet-400 to-purple-500',
  'from-pink-400 to-fuchsia-500',
  'from-red-400 to-orange-500',
];

const ICONS = ['🌱', '🌊', '⛰️', '🌳', '🌈', '🍭', '⭐', '🎯', '🔥', '🏆'];

export default function LevelSelect({
  onPick,
  onBack,
}: {
  onPick: (levelId: string) => void;
  onBack: () => void;
}) {
  return (
    <div className="h-screen w-full overflow-y-auto bg-gradient-to-b from-sky-400 via-sky-200 to-emerald-100 py-8 px-4">
      <div className="max-w-3xl mx-auto pb-16">

        {/* Header */}
        <header className="text-center mb-10">
          <h1
            dir="rtl"
            className="font-arabic text-4xl md:text-5xl font-black text-slate-800 drop-shadow-[0_3px_0_rgba(255,255,255,0.85)]"
          >
            اختر مرحلة
          </h1>
          <p className="font-display text-slate-600 font-semibold mt-2">
            Choose your adventure
          </p>
        </header>

        {/* Grid of level cards */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {levels.map((lvl, i) => {
            const p = progress.get(lvl.id);
            const stars = p?.stars ?? 0;
            const best = p?.bestTimeMs;

            return (
              <button
                key={lvl.id}
                onClick={() => onPick(lvl.id)}
                className={`
                  group relative aspect-square
                  rounded-3xl border-4 border-white/95
                  bg-gradient-to-b ${GRADIENTS[i % 10]}
                  shadow-[0_6px_0_rgba(0,0,0,0.18),0_12px_24px_rgba(0,0,0,0.12)]
                  hover:-translate-y-1.5 hover:shadow-[0_10px_0_rgba(0,0,0,0.18),0_20px_32px_rgba(0,0,0,0.18)]
                  active:translate-y-0 active:shadow-[0_3px_0_rgba(0,0,0,0.18)]
                  transition-all duration-150
                  p-3 flex flex-col items-center justify-center gap-1
                `}
              >
                {/* Number badge */}
                <span className="
                  absolute -top-3 -left-3
                  h-9 w-9 rounded-full
                  bg-white text-slate-800
                  font-display font-black text-base
                  grid place-items-center
                  shadow-md border-2 border-slate-100
                ">
                  {i + 1}
                </span>

                <div className="text-4xl drop-shadow-sm group-hover:scale-110 transition-transform">
                  {ICONS[i % 10]}
                </div>

                <div
                  dir="rtl"
                  className="font-arabic text-[13px] font-bold text-white text-center leading-tight drop-shadow-[0_2px_3px_rgba(0,0,0,0.35)] mt-1"
                >
                  {lvl.name}
                </div>

                <div className="flex gap-0.5 text-base mt-1">
                  {[0, 1, 2].map(s => (
                    <span key={s} className={s < stars ? 'opacity-100' : 'opacity-30'}>
                      ⭐
                    </span>
                  ))}
                </div>

                {best !== undefined && (
                  <div className="text-[10px] font-bold text-white/95 mt-0.5">
                    ⏱ {(best / 1000).toFixed(1)}s
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Back button */}
        <div className="flex justify-center mt-12">
          <button
            onClick={onBack}
            className="
              px-8 py-4 rounded-full
              bg-white text-slate-800
              font-display font-black text-lg
              shadow-[0_6px_0_#94a3b8]
              hover:bg-slate-50
              active:translate-y-1 active:shadow-[0_2px_0_#94a3b8]
              transition-all
              flex items-center gap-2
            "
          >
            <span>←</span>
            <span dir="rtl" className="font-arabic">رجوع</span>
          </button>
        </div>
      </div>
    </div>
  );
}
''', encoding="utf-8")
print("  ✅ LevelSelect.tsx")


print("""
═══════════════════════════════════════════
✅ Tailwind installed + menus redesigned.
═══════════════════════════════════════════

Next:
  1. Stop the dev server (Ctrl+C)
  2. npm run dev -- --host
  3. Hard-reload the browser (Ctrl+Shift+R)

If Tailwind classes don't apply on first load,
just save any .tsx file once to trigger a rebuild.
""")