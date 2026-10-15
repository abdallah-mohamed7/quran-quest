// src/game/types.ts
export type PageAudio = { page: number; file: string };

export type Rect = { x: number; y: number; w: number; h: number };

export type Theme = 'day' | 'sunset' | 'forest' | 'candy' | 'ocean';

export type LevelDef = {
  id: string;
  name: string;
  theme?: Theme;
  startPage: number;
  endPage: number;
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
