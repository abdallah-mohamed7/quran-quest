import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.amaha.quranquest',
  appName: 'Quran Quest',
  webDir: 'dist',
  android: {
    allowMixedContent: true,
    backgroundColor: '#9cd4ff',
  },
  server: {
    androidScheme: 'https',
  },
};

export default config;
