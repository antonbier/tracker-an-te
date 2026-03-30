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

      // Inline the service worker registration — most reliable method
      injectRegister: 'inline',

      manifest: {
        name: 'WanderSuite',
        short_name: 'WanderSuite',
        description: 'Self-hosted Reise- und Budget-Tracker',
        theme_color: '#D95D39',
        background_color: '#12141c',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        lang: 'de',
        icons: [
          {
            src: '/icons/icon-192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: '/icons/icon-512.png',
            sizes: '512x512',
            type: 'image/png',
          },
          {
            // Maskable icon required for Android install prompt
            src: '/icons/icon-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
        shortcuts: [
          {
            name: 'Preis-Radar',
            short_name: 'Radar',
            url: '/',
            icons: [{ src: '/icons/icon-192.png', sizes: '192x192' }],
          },
          {
            name: 'Meine Reisen',
            short_name: 'Reisen',
            url: '/',
            icons: [{ src: '/icons/icon-192.png', sizes: '192x192' }],
          },
        ],
      },

      workbox: {
        // Cache all build assets
        globPatterns: ['**/*.{js,css,html,ico,png,svg,webp,woff2}'],
        // SPA fallback
        navigateFallback: '/',
        navigateFallbackDenylist: [/^\/api/, /^\/health/],
        // Never cache API calls
        runtimeCaching: [
          {
            urlPattern: /^\/api\//,
            handler: 'NetworkOnly',
          },
          {
            urlPattern: /^\/health/,
            handler: 'NetworkOnly',
          },
        ],
        cleanupOutdatedCaches: true,
        skipWaiting: true,
        clientsClaim: true,
      },

      devOptions: {
        enabled: false,
      },
    }),
  ],
});
