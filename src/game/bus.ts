import Phaser from 'phaser';
import type { LevelDef } from './types';

export const bus = new Phaser.Events.EventEmitter();
export const state = { currentLevel: null as LevelDef | null };
