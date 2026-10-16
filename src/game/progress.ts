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
    const r = localStorage.getItem(KEY);
    return r ? JSON.parse(r) : {};
  } catch { return {}; }
}
function save(p: ProgressMap) {
  try { localStorage.setItem(KEY, JSON.stringify(p)); } catch {}
}

export const progress = {
  getAll(): ProgressMap { return load(); },
  get(id: string): LevelProgress | undefined { return load()[id]; },
  record(id: string, stars: number, timeMs: number, coins: number): LevelProgress {
    const all = load();
    const prev = all[id];
    const s = Math.max(0, Math.min(3, stars)) as 0 | 1 | 2 | 3;
    const next: LevelProgress = {
      stars: prev ? (Math.max(prev.stars, s) as 0 | 1 | 2 | 3) : s,
      bestTimeMs: prev ? Math.min(prev.bestTimeMs, timeMs) : timeMs,
      coinsCollected: prev ? Math.max(prev.coinsCollected, coins) : coins,
      completed: true,
    };
    all[id] = next;
    save(all);
    return next;
  },
  clear(): void { localStorage.removeItem(KEY); },
};

export function computeStars(coins: number, total: number, timeMs: number): number {
  let s = 1;
  if (total > 0 && coins / total >= 0.6) s++;
  if (timeMs < 90000) s++;
  return s;
}
