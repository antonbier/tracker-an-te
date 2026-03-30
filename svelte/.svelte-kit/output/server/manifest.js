export const manifest = (() => {
function __memo(fn) {
	let value;
	return () => value ??= (value = fn());
}

return {
	appDir: "_app",
	appPath: "_app",
	assets: new Set([]),
	mimeTypes: {},
	_: {
		client: {start:"_app/immutable/entry/start.hWWsBu9I.js",app:"_app/immutable/entry/app.BiKD_33a.js",imports:["_app/immutable/entry/start.hWWsBu9I.js","_app/immutable/chunks/_R_RGZg6.js","_app/immutable/chunks/DOR8tPSD.js","_app/immutable/entry/app.BiKD_33a.js","_app/immutable/chunks/DOR8tPSD.js","_app/immutable/chunks/L9wIMAJ7.js","_app/immutable/chunks/lbvr6h2N.js","_app/immutable/chunks/B69hbqLP.js"],stylesheets:[],fonts:[],uses_env_dynamic_public:false},
		nodes: [
			__memo(() => import('./nodes/0.js')),
			__memo(() => import('./nodes/1.js')),
			__memo(() => import('./nodes/2.js'))
		],
		remotes: {
			
		},
		routes: [
			{
				id: "/",
				pattern: /^\/$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 2 },
				endpoint: null
			}
		],
		prerendered_routes: new Set([]),
		matchers: async () => {
			
			return {  };
		},
		server_assets: {}
	}
}
})();
