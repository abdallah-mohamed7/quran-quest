// src/game/systems/QuranAudio.ts
import type { PageAudio } from '../types';

export class QuranAudio extends EventTarget {
  private el = new Audio();
  private queue: PageAudio[] = [];
  private index = 0;
  private started = false;
  private armed = false;

  constructor() {
    super();
    this.el.volume = 0.5;
    this.el.preload = 'auto';
    this.el.addEventListener('ended', () => this.next());
    this.el.addEventListener('play',  () => this.dispatchEvent(new Event('play')));
    this.el.addEventListener('pause', () => this.dispatchEvent(new Event('pause')));
  }

  load(pages: PageAudio[]): void {
    this.queue = pages;
    this.index = 0;
  }

  async start(): Promise<void> {
    if (!this.queue.length) return;
    this.started = true;
    this.armed = true;
    await this.playCurrent();
  }

  async resume(): Promise<void> {
    if (!this.started || !this.armed) return this.start();
    try { await this.el.play(); } catch (e) { console.warn('resume blocked:', e); }
  }

  pause(): void { try { this.el.pause(); } catch {} }

  setVolume(v: number): void {
    this.el.volume = Math.max(0, Math.min(1, v));
  }

  get current(): PageAudio | undefined { return this.queue[this.index]; }

  private async playCurrent(): Promise<void> {
    const cur = this.current;
    if (!cur) return;
    this.el.src = cur.file.startsWith('/') ? cur.file.slice(1) : cur.file;
    try {
      await this.el.play();
      this.dispatchEvent(new CustomEvent<PageAudio>('page', { detail: cur }));
    } catch {
      // Autoplay blocked or file missing — silent, no crash.
      this.dispatchEvent(new CustomEvent<PageAudio>('page', { detail: cur }));
    }
  }

  private next(): void {
    if (this.queue.length === 0) return;
    this.index = (this.index + 1) % this.queue.length;
    void this.playCurrent();
  }
}

export const quranAudio = new QuranAudio();
