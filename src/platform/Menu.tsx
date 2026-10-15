// src/platform/Menu.tsx
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
