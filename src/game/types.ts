export type Rect = { x: number; y: number; w: number; h: number };
export type Theme = 'day' | 'sunset' | 'forest' | 'candy' | 'ocean';

export type Decoration = { x: number; y: number; kind: 'tree' | 'bush' };

export type LevelDef = {
  id: string;
  name: string;
  theme: Theme;
  surah: number;
  spawn: { x: number; y: number };
  platforms: Rect[];
  hazards: Rect[];
  coins: { x: number; y: number }[];
  goal: Rect;
  decorations: Decoration[];
};

export type LevelResult = {
  levelId: string;
  timeMs: number;
  coinsCollected: number;
  coinsTotal: number;
};

export type Ayah = { surah: number; ayah: number; file: string };
