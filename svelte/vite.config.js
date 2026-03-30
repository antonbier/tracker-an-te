import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';
import { SvelteKitPWA } from '@vite-pwa/sveltekit';

export default defineConfig({
  plugins: [
    tailwindcss(),
    sveltekit(),
    SvelteKitPWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'WanderSuite',
        short_name: 'WanderSuite',
        description: 'Reise- und Budget-Tracker',
        theme_color: '#D95D39',
        background_color: '#f9f8f6',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
        ],
        shortcuts: [
          { name: 'Preis-Radar', url: '/#priceradar', icons: [{ src: '/icons/icon-192.png', sizes: '192x192' }] },
          { name: 'Meine Reisen', url: '/#mytrips', icons: [{ src: '/icons/icon-192.png', sizes: '192x192' }] },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,webp}'],
        navigateFallback: 'index.html',
        runtimeCaching: [
          {
            urlPattern: /^\/api\//,
            handler: 'NetworkOnly',   // Never cache API calls
          },
        ],
      },
      devOptions: {
        enabled: false,
      },
    }),
  ],
});
