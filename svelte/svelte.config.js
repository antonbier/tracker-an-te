import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  kit: {
    adapter: adapter({
      pages: 'dist',
      assets: 'dist',
      fallback: 'index.html',   // SPA fallback
      precompress: false,
    }),
    // No base path needed for here.now root deployment
  },
};

export default config;
