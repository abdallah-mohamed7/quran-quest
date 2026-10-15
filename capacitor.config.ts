import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.amaha.quranquest',
  appName: 'Quran Quest',
  webDir: 'dist',
  android: {
    allowMixedContent: true,
  },
};

export default config;
