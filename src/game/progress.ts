// src/game/progress.ts
const KEY = 'quran-quest-progress';

export type LevelProgress = {
  stars: 0 | 1 | 2 | 3;
  bestTimeMs: number;
  coinsCollected: number;
  completed: boolean;
};

export type ProgressMap = Record<string, LevelProgress>;

function load(): ProgressMap {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) as ProgressMap : {};
  } catch { return {}; }
}

function save(p: ProgressMap): void {
  try { localStorage.setItem(KEY, JSON.stringify(p)); } catch {}
}

export const progress = {
  get(levelId: string): LevelProgress | undefined {
    return load()[levelId];
  },
  record(levelId: string, stars: number, timeMs: number, coinsCollected: number): LevelProgress {
    const all = load();
    const prev = all[levelId];
    const cs = Math.max(0, Math.min(3, stars)) as 0 | 1 | 2 | 3;
    const next: LevelProgress = {
      stars: prev ? (Math.max(prev.stars, cs) as 0 | 1 | 2 | 3) : cs,
      bestTimeMs: prev ? Math.min(prev.bestTimeMs, timeMs) : timeMs,
      coinsCollected: prev ? Math.max(prev.coinsCollected, coinsCollected) : coinsCollected,
      completed: true,
    };
    all[levelId] = next;
    save(all);
    return next;
  },
  clear(): void { localStorage.removeItem(KEY); },
};

export function computeStars(coinsGot: number, coinsTotal: number, timeMs: number): number {
  let s = 1;
  if (coinsTotal > 0 && coinsGot / coinsTotal >= 0.6) s++;
  if (timeMs < 60000) s++;
  return s;
}
