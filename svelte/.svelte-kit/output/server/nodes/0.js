

export const index = 0;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_layout.svelte.js')).default;
export const universal = {
  "prerender": false,
  "ssr": false
};
export const universal_id = "src/routes/+layout.js";
export const imports = ["_app/immutable/nodes/0.jHH7stiX.js","_app/immutable/chunks/L9wIMAJ7.js","_app/immutable/chunks/DOR8tPSD.js","_app/immutable/chunks/lbvr6h2N.js","_app/immutable/chunks/CEde95eK.js","_app/immutable/chunks/J3-LsDVV.js","_app/immutable/chunks/BqbTizjn.js","_app/immutable/chunks/B69hbqLP.js"];
export const stylesheets = ["_app/immutable/assets/0.MymB7vrJ.css"];
export const fonts = [];
