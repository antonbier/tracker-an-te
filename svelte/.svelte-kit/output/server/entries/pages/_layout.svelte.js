import { e as ensure_array_like, s as store_get, a as attr_class, b as stringify, c as escape_html, u as unsubscribe_stores, d as attr_style, f as bind_props, g as attr } from "../../chunks/index2.js";
import { i as isDark, c as currentPage, o as onboardingDone, a as apiUrl } from "../../chunks/stores.js";
import { w as writable } from "../../chunks/index.js";
import "clsx";
const toasts = writable([]);
function Toast($$renderer) {
  var $$store_subs;
  const typeStyles = {
    success: "bg-green-600",
    error: "bg-red-600",
    warning: "bg-amber-500",
    info: "bg-blue-600"
  };
  $$renderer.push(`<div class="fixed bottom-20 md:bottom-6 right-4 z-50 flex flex-col gap-2 pointer-events-none"><!--[-->`);
  const each_array = ensure_array_like(store_get($$store_subs ??= {}, "$toasts", toasts));
  for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
    let t = each_array[$$index];
    $$renderer.push(`<div${attr_class(`px-4 py-2.5 rounded-xl text-white text-sm font-medium shadow-lg pointer-events-auto ${stringify(typeStyles[t.type] ?? typeStyles.info)}`)}>${escape_html(t.message)}</div>`);
  }
  $$renderer.push(`<!--]--></div>`);
  if ($$store_subs) unsubscribe_stores($$store_subs);
}
function Header($$renderer, $$props) {
  var $$store_subs;
  $$renderer.push(`<header class="flex items-center justify-between px-4 h-14 border-b shrink-0" style="background:var(--ws-surface);border-color:var(--ws-border)"><div class="flex items-center gap-2"><span class="text-xl">🧭</span> <span class="font-semibold tracking-tight" style="color:var(--ws-accent)">WanderSuite</span></div> <div class="flex items-center gap-1"><button class="p-2 rounded-lg hover:opacity-70 transition-opacity" title="Dark Mode umschalten">${escape_html(store_get($$store_subs ??= {}, "$isDark", isDark) ? "☀️" : "🌙")}</button> <button class="p-2 rounded-lg hover:opacity-70 transition-opacity" title="Hilfe">📖</button> <button class="p-2 rounded-lg hover:opacity-70 transition-opacity" title="Einstellungen">⚙️</button></div></header>`);
  if ($$store_subs) unsubscribe_stores($$store_subs);
}
function Sidebar($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    const nav = [
      { id: "home", icon: "🏠", label: "Dashboard" },
      { id: "priceradar", icon: "🎯", label: "Preis-Radar" },
      { id: "discover", icon: "✨", label: "Discover" },
      { id: "mytrips", icon: "🎒", label: "Meine Reisen" }
    ];
    $$renderer2.push(`<aside class="hidden md:flex flex-col w-56 shrink-0 border-r" style="background:var(--ws-surface);border-color:var(--ws-border)"><nav class="flex-1 p-3 flex flex-col gap-1 pt-4"><!--[-->`);
    const each_array = ensure_array_like(nav);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let item = each_array[$$index];
      $$renderer2.push(`<button${attr_class("flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors text-left w-full", void 0, {
        "active": store_get($$store_subs ??= {}, "$currentPage", currentPage) === item.id
      })}${attr_style(store_get($$store_subs ??= {}, "$currentPage", currentPage) === item.id ? "background:var(--ws-accent);color:#fff" : "color:var(--ws-muted)")}><span class="text-base">${escape_html(item.icon)}</span> ${escape_html(item.label)}</button>`);
    }
    $$renderer2.push(`<!--]--></nav> <div class="p-3 border-t" style="border-color:var(--ws-border)"><button class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium w-full transition-colors" style="color:var(--ws-muted)"><span class="text-base">⚙️</span> Einstellungen</button></div></aside>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function BottomNav($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    const nav = [
      { id: "home", icon: "🏠", label: "Home" },
      { id: "priceradar", icon: "🎯", label: "Radar" },
      { id: "discover", icon: "✨", label: "Discover" },
      { id: "mytrips", icon: "🎒", label: "Reisen" }
    ];
    $$renderer2.push(`<nav class="md:hidden flex border-t shrink-0" style="background:var(--ws-surface);border-color:var(--ws-border)"><!--[-->`);
    const each_array = ensure_array_like(nav);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let item = each_array[$$index];
      $$renderer2.push(`<button class="flex-1 flex flex-col items-center justify-center py-2 gap-0.5 text-xs font-medium transition-colors"${attr_style(store_get($$store_subs ??= {}, "$currentPage", currentPage) === item.id ? "color:var(--ws-accent)" : "color:var(--ws-muted)")}><span class="text-lg leading-none">${escape_html(item.icon)}</span> ${escape_html(item.label)}</button>`);
    }
    $$renderer2.push(`<!--]--></nav>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function FieldGuide($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { open = false } = $$props;
    let activeTab = "start";
    const tabs = [
      { id: "start", label: "🚀 Start" },
      { id: "radar", label: "🎯 Preis-Radar" },
      { id: "reisen", label: "🎒 Reisen" },
      { id: "settings", label: "⚙️ Setup" }
    ];
    if (open) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="fixed inset-0 z-40 bg-black/40 cursor-default" role="button" tabindex="-1" aria-label="Schließen"></div> <div class="fixed inset-y-0 right-0 z-50 w-full max-w-md flex flex-col shadow-2xl" style="background:var(--ws-surface)"><div class="flex items-center justify-between px-5 py-4 border-b" style="border-color:var(--ws-border)"><h2 class="font-semibold text-lg">📖 Field Guide</h2> <button class="p-1.5 rounded-lg hover:opacity-60">✕</button></div> <div class="flex border-b px-4 gap-1 pt-2" style="border-color:var(--ws-border)"><!--[-->`);
      const each_array = ensure_array_like(tabs);
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let tab = each_array[$$index];
        $$renderer2.push(`<button class="px-3 py-2 text-sm rounded-t-lg font-medium transition-colors"${attr_style(activeTab === tab.id ? "color:var(--ws-accent);border-bottom:2px solid var(--ws-accent)" : "color:var(--ws-muted)")}>${escape_html(tab.label)}</button>`);
      }
      $$renderer2.push(`<!--]--></div> <div class="flex-1 overflow-y-auto p-5 text-sm" style="color:var(--ws-text)">`);
      {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<h3 class="font-semibold mb-2">Willkommen bei WanderSuite 👋</h3> <p style="color:var(--ws-muted)">Gib im ersten Schritt deine Backend-URL in den Einstellungen ein.</p>`);
      }
      $$renderer2.push(`<!--]--></div></div>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]-->`);
    bind_props($$props, { open });
  });
}
function Settings($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { open = false } = $$props;
    let activeTab = "basic";
    let urlInput = "";
    let testing = false;
    const tabs = [
      { id: "basic", label: "⚙️ Allgemein" },
      { id: "integrations", label: "🔗 Integrationen" },
      { id: "apis", label: "🤖 APIs & KI" },
      { id: "notifications", label: "🔔 Alerts" }
    ];
    if (open) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="fixed inset-0 z-40 bg-black/40 cursor-default" role="button" tabindex="-1" aria-label="Schließen"></div> <div class="fixed inset-y-0 right-0 z-50 w-full max-w-md flex flex-col shadow-2xl" style="background:var(--ws-surface)"><div class="flex items-center justify-between px-5 py-4 border-b" style="border-color:var(--ws-border)"><h2 class="font-semibold text-lg">Einstellungen</h2> <button class="p-1.5 rounded-lg hover:opacity-60">✕</button></div> <div class="flex border-b px-2 gap-1 pt-2 overflow-x-auto" style="border-color:var(--ws-border)"><!--[-->`);
      const each_array = ensure_array_like(tabs);
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let tab = each_array[$$index];
        $$renderer2.push(`<button class="px-3 py-2 text-xs rounded-t-lg font-medium whitespace-nowrap transition-colors shrink-0"${attr_style(activeTab === tab.id ? "color:var(--ws-accent);border-bottom:2px solid var(--ws-accent)" : "color:var(--ws-muted)")}>${escape_html(tab.label)}</button>`);
      }
      $$renderer2.push(`<!--]--></div> <div class="flex-1 overflow-y-auto p-5">`);
      {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<label class="block mb-1 text-sm font-medium">Backend URL</label> <input type="url"${attr("value", urlInput)} placeholder="https://..." class="w-full px-3 py-2 rounded-xl border text-sm mb-3" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/> <div class="flex gap-2"><button${attr("disabled", testing, true)} class="px-4 py-2 rounded-xl text-sm border transition-opacity hover:opacity-70" style="border-color:var(--ws-border);color:var(--ws-muted)">${escape_html("🔗 Verbindung testen")}</button> `);
        {
          $$renderer2.push("<!--[-1-->");
        }
        $$renderer2.push(`<!--]--></div>`);
      }
      $$renderer2.push(`<!--]--></div> <div class="p-4 border-t" style="border-color:var(--ws-border)"><button class="w-full py-2.5 rounded-xl text-sm font-semibold text-white transition-opacity hover:opacity-90" style="background:var(--ws-accent)">Speichern</button></div></div>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]-->`);
    bind_props($$props, { open });
  });
}
function AppShell($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { children } = $$props;
    let fieldGuideOpen = false;
    let settingsOpen = false;
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<div class="flex h-screen overflow-hidden" style="background:var(--ws-bg);color:var(--ws-text)">`);
      Sidebar($$renderer3);
      $$renderer3.push(`<!----> <div class="flex flex-col flex-1 min-w-0 overflow-hidden">`);
      Header($$renderer3);
      $$renderer3.push(`<!----> <main class="flex-1 overflow-y-auto p-4 md:p-6">`);
      children($$renderer3);
      $$renderer3.push(`<!----></main> `);
      BottomNav($$renderer3);
      $$renderer3.push(`<!----></div></div> `);
      FieldGuide($$renderer3, {
        get open() {
          return fieldGuideOpen;
        },
        set open($$value) {
          fieldGuideOpen = $$value;
          $$settled = false;
        }
      });
      $$renderer3.push(`<!----> `);
      Settings($$renderer3, {
        get open() {
          return settingsOpen;
        },
        set open($$value) {
          settingsOpen = $$value;
          $$settled = false;
        }
      });
      $$renderer3.push(`<!---->`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
  });
}
function Onboarding($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let step = 1;
    let urlInput = "";
    $$renderer2.push(`<div class="fixed inset-0 z-50 flex items-center justify-center p-4" style="background:var(--ws-bg)"><div class="w-full max-w-sm"><div class="text-center mb-8"><div class="text-5xl mb-3">🧭</div> <h1 class="text-2xl font-bold" style="color:var(--ws-accent)">WanderSuite</h1> <p class="text-sm mt-1" style="color:var(--ws-muted)">Schritt ${escape_html(step)} von 3</p></div> <div class="h-1 rounded-full mb-8" style="background:var(--ws-border)"><div class="h-1 rounded-full transition-all"${attr_style(`background:var(--ws-accent);width:${stringify(step / 3 * 100)}%`)}></div></div> `);
    {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<h2 class="font-semibold text-lg mb-1">Backend verbinden</h2> <p class="text-sm mb-4" style="color:var(--ws-muted)">Gib die URL deines WanderSuite-Backends ein.</p> <input type="url"${attr("value", urlInput)} placeholder="https://dein-backend.railway.app" class="w-full px-4 py-3 rounded-xl border text-sm mb-3" style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)"/> `);
      {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--> <button${attr("disabled", !urlInput, true)} class="w-full py-3 rounded-xl text-sm font-semibold mb-3 transition-opacity" style="background:var(--ws-surface2);color:var(--ws-text)">${escape_html("🔗 Verbindung testen")}</button> <button${attr("disabled", true, true)} class="w-full py-3 rounded-xl text-sm font-semibold text-white transition-opacity"${attr_style(`background:var(--ws-accent);opacity:${stringify(0.4)}`)}>Weiter →</button>`);
    }
    $$renderer2.push(`<!--]--> <button class="w-full text-center text-xs mt-4 py-2" style="color:var(--ws-muted)">Überspringen</button></div></div>`);
  });
}
function _layout($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let { children } = $$props;
    if (!store_get($$store_subs ??= {}, "$onboardingDone", onboardingDone) && !store_get($$store_subs ??= {}, "$apiUrl", apiUrl)) {
      $$renderer2.push("<!--[0-->");
      Onboarding($$renderer2);
    } else {
      $$renderer2.push("<!--[-1-->");
      AppShell($$renderer2, {
        children: ($$renderer3) => {
          children($$renderer3);
          $$renderer3.push(`<!---->`);
        }
      });
    }
    $$renderer2.push(`<!--]--> `);
    Toast($$renderer2);
    $$renderer2.push(`<!---->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _layout as default
};
