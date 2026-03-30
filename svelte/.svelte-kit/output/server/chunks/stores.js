import { d as derived, w as writable } from "./index.js";
function persisted(key, defaultValue) {
  const initial = defaultValue;
  const store = writable(initial);
  return store;
}
const apiUrl = persisted("apiUrl", "");
const theme = persisted("theme", "");
const onboardingDone = persisted("ws-onboarding-done", "");
const currentPage = writable("home");
const trips = writable([]);
const budget = writable(null);
const isDark = derived(theme, ($t) => $t === "dark");
derived(apiUrl, ($url) => $url.length > 0);
export {
  apiUrl as a,
  budget as b,
  currentPage as c,
  isDark as i,
  onboardingDone as o,
  trips as t
};
