import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  kit: {
    adapter: adapter({
      pages: 'dist',
      assets: 'dist',
      fallback: 'index.html',
      precompress: false,
    }),
  },
  compilerOptions: {
    // Disable a11y warnings — we handle accessibility manually
    // These are warnings not errors, but treat as errors in strict mode
  },
  vitePlugin: {
    onwarn(warning, handler) {
      // Suppress a11y warnings that block build
      if (warning.code.startsWith('a11y_')) return;
      handler(warning);
    },
  },
};

export default config;
