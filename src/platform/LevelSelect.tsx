// src/platform/LevelSelect.tsx
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
