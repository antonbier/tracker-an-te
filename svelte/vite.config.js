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
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },

      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,webp,woff2}'],

        // Never cache index.html — always fetch fresh so new SW activates
        navigateFallback: null,

        // Exclude API and health from SW
        navigateFallbackDenylist: [/^\/api/, /^\/health/],

        runtimeCaching: [
          {
            // API calls — never cache
            urlPattern: /^\/api\//,
            handler: 'NetworkOnly',
          },
          {
            // index.html — always network first, no cache
            urlPattern: ({ request }) => request.mode === 'navigate',
            handler: 'NetworkFirst',
            options: {
              cacheName: 'pages',
              networkTimeoutSeconds: 3,
            },
          },
        ],

        cleanupOutdatedCaches: true,
        skipWaiting: true,
        clientsClaim: true,
      },

      devOptions: { enabled: false },
    }),
  ],
});
