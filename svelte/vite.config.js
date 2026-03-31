import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [
    tailwindcss(),
    sveltekit(),
    // PWA Plugin disabled — Service Worker caused click-blocking issues on here.now.
    // PWA works on Unraid (Nginx serves sw.js correctly with proper headers).
    // To re-enable: uncomment and install @vite-pwa/sveltekit
  ],
});
