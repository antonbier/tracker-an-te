import { e as ensure_array_like, c as escape_html, d as attr_style, b as stringify, g as attr, a9 as derived, s as store_get, u as unsubscribe_stores } from "../../chunks/index2.js";
import { b as budget, t as trips, c as currentPage } from "../../chunks/stores.js";
function Dashboard($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let trackers = [];
    const totalBudget = derived(() => store_get($$store_subs ??= {}, "$budget", budget) ? parseFloat(store_get($$store_subs ??= {}, "$budget", budget)) : 0);
    const totalSpent = derived(() => store_get($$store_subs ??= {}, "$trips", trips).reduce((s, t) => s + (parseFloat(t.cost) || 0), 0));
    const remaining = derived(() => Math.max(0, totalBudget() - totalSpent()));
    const spentPct = derived(() => totalBudget() > 0 ? Math.min(100, totalSpent() / totalBudget() * 100) : 0);
    const CIRC = 2 * Math.PI * 38;
    const donutFill = derived(() => spentPct() / 100 * CIRC);
    const donutColor = derived(() => spentPct() > 85 ? "var(--ws-red)" : spentPct() > 60 ? "var(--ws-accent2)" : "var(--ws-accent)");
    const activeTrackers = derived(() => trackers.filter((t) => t.active));
    const today = (/* @__PURE__ */ new Date()).toISOString().slice(0, 10);
    const upcoming = derived(() => store_get($$store_subs ??= {}, "$trips", trips).filter((t) => t.date >= today));
    const completed = derived(() => store_get($$store_subs ??= {}, "$trips", trips).filter((t) => t.date < today));
    $$renderer2.push(`<div class="space-y-4"><div><h1 class="text-2xl font-bold italic" style="font-family:var(--ws-serif);color:var(--ws-text)">Willkommen zurück</h1> <p class="text-sm mt-0.5" style="color:var(--ws-muted)">Dein Reise-Überblick</p></div> <div class="grid grid-cols-3 gap-3"><!--[-->`);
    const each_array = ensure_array_like([
      {
        label: "Aktive Tracker",
        value: activeTrackers().length,
        color: "var(--ws-accent)"
      },
      {
        label: "Jahresbudget",
        value: totalBudget() > 0 ? totalBudget().toFixed(0) + " €" : "–",
        color: "var(--ws-accent2)"
      },
      {
        label: "Verbleibend",
        value: totalBudget() > 0 ? remaining().toFixed(0) + " €" : "–",
        color: "var(--ws-green)"
      }
    ]);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let s = each_array[$$index];
      $$renderer2.push(`<div class="rounded-xl p-3 border" style="background:var(--ws-surface);border-color:var(--ws-border)"><div class="text-xs font-bold tracking-widest uppercase mb-1" style="color:var(--ws-muted);font-family:var(--ws-mono)">${escape_html(s.label)}</div> <div class="text-2xl font-bold"${attr_style(`color:${stringify(s.color)};font-family:var(--ws-serif)`)}>${escape_html(s.value)}</div></div>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="grid md:grid-cols-2 gap-4"><div class="rounded-xl p-4 border" style="background:var(--ws-surface);border-color:var(--ws-border)"><h2 class="text-sm font-semibold italic mb-3" style="font-family:var(--ws-serif);color:var(--ws-accent2)">💰 Budget-Übersicht</h2> <div class="flex items-center gap-4"><svg width="90" height="90" viewBox="0 0 100 100"><circle cx="50" cy="50" r="38" fill="none" stroke="var(--ws-border)" stroke-width="14"></circle><circle cx="50" cy="50" r="38" fill="none"${attr("stroke", donutColor())} stroke-width="14"${attr("stroke-dasharray", `${stringify(donutFill())} ${stringify(CIRC - donutFill())}`)} stroke-dashoffset="60" stroke-linecap="round" style="transition: stroke-dasharray .6s ease"></circle></svg> <div class="flex-1 space-y-1.5 text-xs"><!--[-->`);
    const each_array_1 = ensure_array_like([
      {
        dot: "var(--ws-accent)",
        label: "Ausgegeben",
        val: totalSpent().toFixed(2) + " €"
      },
      {
        dot: "var(--ws-green)",
        label: "Verbleibend",
        val: remaining().toFixed(2) + " €"
      },
      {
        dot: "var(--ws-border)",
        label: "Jahresbudget",
        val: totalBudget().toFixed(2) + " €"
      }
    ]);
    for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
      let row = each_array_1[$$index_1];
      $$renderer2.push(`<div class="flex items-center gap-2"><div class="w-2.5 h-2.5 rounded-full shrink-0"${attr_style(`background:${stringify(row.dot)}`)}></div> <span style="color:var(--ws-muted)">${escape_html(row.label)}</span> <span class="ml-auto font-bold font-mono" style="color:var(--ws-text)">${escape_html(row.val)}</span></div>`);
    }
    $$renderer2.push(`<!--]--></div></div></div> <div class="rounded-xl p-4 border" style="background:var(--ws-surface);border-color:var(--ws-border)"><h2 class="text-sm font-semibold italic mb-3" style="font-family:var(--ws-serif);color:var(--ws-accent2)">🎯 Aktive Tracker</h2> `);
    {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<p class="text-xs" style="color:var(--ws-muted)">Lade...</p>`);
    }
    $$renderer2.push(`<!--]--> <button class="mt-3 w-full py-2 rounded-xl text-sm font-semibold transition-opacity hover:opacity-80" style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">+ Tracker starten</button></div></div> <div class="grid md:grid-cols-2 gap-4"><div class="rounded-xl p-4 border" style="background:var(--ws-surface);border-color:var(--ws-border)"><h2 class="text-sm font-semibold italic mb-3" style="font-family:var(--ws-serif);color:var(--ws-accent2)">✈️ Geplante Reisen</h2> `);
    if (upcoming().length === 0) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<p class="text-xs" style="color:var(--ws-muted)">Keine geplanten Reisen.</p>`);
    } else {
      $$renderer2.push("<!--[-1-->");
      $$renderer2.push(`<div class="space-y-2"><!--[-->`);
      const each_array_3 = ensure_array_like(upcoming());
      for (let $$index_3 = 0, $$length = each_array_3.length; $$index_3 < $$length; $$index_3++) {
        let t = each_array_3[$$index_3];
        $$renderer2.push(`<div class="flex items-center gap-3 p-2 rounded-lg" style="background:var(--ws-surface2)"><span>✈️</span> <div class="flex-1"><div class="text-sm font-semibold italic" style="font-family:var(--ws-serif)">${escape_html(t.name)}</div> <div class="text-xs font-mono" style="color:var(--ws-muted)">${escape_html(t.date)}</div></div> <div class="text-sm font-bold font-mono" style="color:var(--ws-accent2)">${escape_html(parseFloat(t.cost).toFixed(2))} €</div></div>`);
      }
      $$renderer2.push(`<!--]--></div>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="rounded-xl p-4 border" style="background:var(--ws-surface);border-color:var(--ws-border)"><h2 class="text-sm font-semibold italic mb-3" style="font-family:var(--ws-serif);color:var(--ws-accent2)">✅ Abgeschlossen</h2> `);
    if (completed().length === 0) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<p class="text-xs" style="color:var(--ws-muted)">Noch keine abgeschlossenen Reisen.</p>`);
    } else {
      $$renderer2.push("<!--[-1-->");
      $$renderer2.push(`<div class="space-y-2"><!--[-->`);
      const each_array_4 = ensure_array_like(completed().slice(0, 4));
      for (let $$index_4 = 0, $$length = each_array_4.length; $$index_4 < $$length; $$index_4++) {
        let t = each_array_4[$$index_4];
        $$renderer2.push(`<div class="flex items-center gap-3 p-2 rounded-lg opacity-70" style="background:var(--ws-surface2)"><span>✅</span> <div class="flex-1"><div class="text-sm font-semibold italic" style="font-family:var(--ws-serif)">${escape_html(t.name)}</div> <div class="text-xs font-mono" style="color:var(--ws-muted)">${escape_html(t.date)}</div></div> <div class="text-sm font-bold font-mono" style="color:var(--ws-muted)">${escape_html(parseFloat(t.cost).toFixed(2))} €</div></div>`);
      }
      $$renderer2.push(`<!--]--></div>`);
    }
    $$renderer2.push(`<!--]--></div></div></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function PriceRadar($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let activeTab = "ryanair";
    let origin = "BGY";
    let destination = "DUB";
    const today = /* @__PURE__ */ new Date();
    const d30 = new Date(today);
    d30.setDate(d30.getDate() + 30);
    const d37 = new Date(today);
    d37.setDate(d37.getDate() + 37);
    let outbound = d30.toISOString().slice(0, 10);
    let returnDate = d37.toISOString().slice(0, 10);
    let adults = 2;
    let children = 0;
    let seatCost = 0;
    let bags = [];
    let adding = false;
    const bagOptions = [
      { type: "10kg", label: "10 kg Check-in Koffer" },
      { type: "20kg", label: "20 kg Check-in Koffer" },
      { type: "23kg", label: "23 kg Koffer (Large)" }
    ];
    const tabs = [
      { id: "ryanair", label: "🟠 Ryanair" },
      { id: "gflights", label: "🔵 Google Flights" },
      { id: "homair", label: "⛺ Homair" },
      { id: "booking", label: "🏨 Booking" }
    ];
    $$renderer2.push(`<div class="space-y-4"><h1 class="text-2xl font-bold italic" style="font-family:var(--ws-serif)">🎯 Preis-Radar</h1> <div class="flex gap-1 overflow-x-auto pb-1"><!--[-->`);
    const each_array = ensure_array_like(tabs);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let tab = each_array[$$index];
      $$renderer2.push(`<button class="px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all border"${attr_style(activeTab === tab.id ? "background:var(--ws-accent);color:#fff5ec;border-color:var(--ws-accent)" : "background:var(--ws-surface);color:var(--ws-muted);border-color:var(--ws-border)")}>${escape_html(tab.label)}</button>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="grid md:grid-cols-2 gap-4"><div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)"><h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">Neuen Tracker anlegen</h2> <div class="grid grid-cols-2 gap-2"><div><label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Von (IATA)</label> <input${attr("value", origin)} maxlength="3" placeholder="BGY" class="w-full mt-1 px-3 py-2 rounded-xl border text-sm font-mono uppercase" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/></div> <div><label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Nach (IATA)</label> <input${attr("value", destination)} maxlength="3" placeholder="DUB" class="w-full mt-1 px-3 py-2 rounded-xl border text-sm font-mono uppercase" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/></div></div> <div class="grid grid-cols-2 gap-2"><div><label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Hinflug</label> <input type="date"${attr("value", outbound)} class="w-full mt-1 px-3 py-2 rounded-xl border text-sm" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/></div> <div><label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Rückflug (opt.)</label> <input type="date"${attr("value", returnDate)} class="w-full mt-1 px-3 py-2 rounded-xl border text-sm" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/></div></div> <div class="grid grid-cols-2 gap-2"><div><label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Erwachsene</label> `);
      $$renderer2.select(
        {
          value: adults,
          class: "w-full mt-1 px-3 py-2 rounded-xl border text-sm",
          style: "background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"
        },
        ($$renderer3) => {
          $$renderer3.push(`<!--[-->`);
          const each_array_1 = ensure_array_like([1, 2, 3, 4, 5, 6]);
          for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
            let n = each_array_1[$$index_1];
            $$renderer3.option({ value: n }, ($$renderer4) => {
              $$renderer4.push(`${escape_html(n)}`);
            });
          }
          $$renderer3.push(`<!--]-->`);
        }
      );
      $$renderer2.push(`</div> <div><label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Kinder</label> `);
      $$renderer2.select(
        {
          value: children,
          class: "w-full mt-1 px-3 py-2 rounded-xl border text-sm",
          style: "background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"
        },
        ($$renderer3) => {
          $$renderer3.push(`<!--[-->`);
          const each_array_2 = ensure_array_like([0, 1, 2, 3, 4]);
          for (let $$index_2 = 0, $$length = each_array_2.length; $$index_2 < $$length; $$index_2++) {
            let n = each_array_2[$$index_2];
            $$renderer3.option({ value: n }, ($$renderer4) => {
              $$renderer4.push(`${escape_html(n)}`);
            });
          }
          $$renderer3.push(`<!--]-->`);
        }
      );
      $$renderer2.push(`</div></div> <div><label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">🧳 Gepäck (pro Person)</label> <div class="mt-1.5 space-y-1.5"><!--[-->`);
      const each_array_3 = ensure_array_like(bagOptions);
      for (let $$index_3 = 0, $$length = each_array_3.length; $$index_3 < $$length; $$index_3++) {
        let b = each_array_3[$$index_3];
        $$renderer2.push(`<button class="w-full flex items-center gap-3 px-3 py-2 rounded-xl border text-sm transition-colors text-left"${attr_style(bags.includes(b.type) ? "background:rgba(196,98,45,.1);border-color:var(--ws-accent);color:var(--ws-text)" : "background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)")}><span class="w-4 h-4 rounded border flex items-center justify-center text-xs"${attr_style(`border-color:${stringify(bags.includes(b.type) ? "var(--ws-accent)" : "var(--ws-border)")}`)}>${escape_html(bags.includes(b.type) ? "✓" : "")}</span> ${escape_html(b.label)}</button>`);
      }
      $$renderer2.push(`<!--]--></div></div> <div><label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">🪑 Sitzplatz (€/Person/Flug)</label> <input type="number"${attr("value", seatCost)} min="0" step="0.01" placeholder="0.00" class="w-full mt-1 px-3 py-2 rounded-xl border text-sm" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/></div> <button${attr("disabled", adding, true)} class="w-full py-2.5 rounded-xl font-semibold text-sm transition-opacity hover:opacity-80 disabled:opacity-50" style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">${escape_html("+ Tracker starten")}</button></div> <div class="space-y-3"><h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">Aktive Tracker</h2> `);
      {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<p class="text-xs" style="color:var(--ws-muted)">Lade…</p>`);
      }
      $$renderer2.push(`<!--]--></div></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function MyTrips($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let activeTab = "overview";
    (/* @__PURE__ */ new Date()).toISOString().slice(0, 10);
    const totalSpent = derived(() => store_get($$store_subs ??= {}, "$trips", trips).reduce((s, t) => s + (parseFloat(t.cost) || 0), 0));
    const totalBudget = derived(() => parseFloat(store_get($$store_subs ??= {}, "$budget", budget)) || 0);
    const pct = derived(() => totalBudget() > 0 ? Math.min(100, totalSpent() / totalBudget() * 100) : 0);
    const tabs = [
      { id: "overview", label: "📊 Übersicht" },
      { id: "trips", label: "✈️ Reisen" },
      { id: "budget", label: "💶 Budget" }
    ];
    $$renderer2.push(`<div class="space-y-4"><h1 class="text-2xl font-bold italic" style="font-family:var(--ws-serif)">🎒 Meine Reisen</h1> <div class="flex gap-1 overflow-x-auto pb-1"><!--[-->`);
    const each_array = ensure_array_like(tabs);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let tab = each_array[$$index];
      $$renderer2.push(`<button class="px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all border"${attr_style(activeTab === tab.id ? "background:var(--ws-accent);color:#fff5ec;border-color:var(--ws-accent)" : "background:var(--ws-surface);color:var(--ws-muted);border-color:var(--ws-border)")}>${escape_html(tab.label)}</button>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="grid md:grid-cols-3 gap-3"><!--[-->`);
      const each_array_1 = ensure_array_like([
        {
          label: "Reisen",
          value: store_get($$store_subs ??= {}, "$trips", trips).length
        },
        {
          label: "Ausgegeben",
          value: totalSpent().toFixed(2) + " €",
          color: "var(--ws-accent)"
        },
        {
          label: "Verbleibend",
          value: totalBudget() > 0 ? Math.max(0, totalBudget() - totalSpent()).toFixed(2) + " €" : "–",
          color: "var(--ws-green)"
        }
      ]);
      for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
        let s = each_array_1[$$index_1];
        $$renderer2.push(`<div class="rounded-xl p-3 border" style="background:var(--ws-surface);border-color:var(--ws-border)"><div class="text-xs font-bold uppercase tracking-wider mb-1" style="color:var(--ws-muted)">${escape_html(s.label)}</div> <div class="text-2xl font-bold"${attr_style(`color:${stringify(s.color ?? "var(--ws-text)")};font-family:var(--ws-serif)`)}>${escape_html(s.value)}</div></div>`);
      }
      $$renderer2.push(`<!--]--></div> `);
      if (totalBudget() > 0) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<div class="rounded-xl p-4 border" style="background:var(--ws-surface);border-color:var(--ws-border)"><div class="flex justify-between text-xs mb-2" style="color:var(--ws-muted)"><span>Budget-Fortschritt</span><span>${escape_html(pct().toFixed(0))}%</span></div> <div class="h-2 rounded-full" style="background:var(--ws-border)"><div class="h-2 rounded-full transition-all"${attr_style(`width:${stringify(pct())}%;background:${stringify(pct() > 85 ? "var(--ws-red)" : pct() > 60 ? "var(--ws-accent2)" : "var(--ws-green)")}`)}></div></div></div>`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function Discover($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let query = "";
    let provider = "gemini";
    let results = [];
    let loading = false;
    typeof localStorage !== "undefined" ? localStorage.getItem("s-geminiKey") || "" : "";
    typeof localStorage !== "undefined" ? localStorage.getItem("s-openaiKey") || "" : "";
    $$renderer2.push(`<div class="space-y-4"><h1 class="text-2xl font-bold italic" style="font-family:var(--ws-serif)">✨ Inspiration</h1> <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)"><div class="grid grid-cols-2 gap-2"><div><label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">KI-Anbieter</label> `);
    $$renderer2.select(
      {
        value: provider,
        class: "w-full mt-1 px-3 py-2 rounded-xl border text-sm",
        style: "background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"
      },
      ($$renderer3) => {
        $$renderer3.option({ value: "gemini" }, ($$renderer4) => {
          $$renderer4.push(`Google Gemini`);
        });
        $$renderer3.option({ value: "openai" }, ($$renderer4) => {
          $$renderer4.push(`OpenAI`);
        });
      }
    );
    $$renderer2.push(`</div></div> <div><label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Was suchst du?</label> <textarea placeholder="z.B. Strand, warmes Wetter, günstig, Oktober..." rows="3" class="w-full mt-1 px-3 py-2 rounded-xl border text-sm resize-none" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">`);
    const $$body = escape_html(query);
    if ($$body) {
      $$renderer2.push(`${$$body}`);
    }
    $$renderer2.push(`</textarea></div> <button${attr("disabled", loading, true)} class="w-full py-2.5 rounded-xl font-semibold text-sm transition-opacity hover:opacity-80 disabled:opacity-50" style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">${escape_html("🌍 Reiseideen generieren")}</button></div> `);
    if (results.length > 0) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="space-y-3"><!--[-->`);
      const each_array = ensure_array_like(results);
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let r = each_array[$$index];
        $$renderer2.push(`<div class="rounded-xl p-4 border" style="background:var(--ws-surface);border-color:var(--ws-border)"><div class="font-bold text-base italic mb-1" style="font-family:var(--ws-serif);color:var(--ws-text)">🌍 ${escape_html(r.destination)}</div> <p class="text-sm mb-2" style="color:var(--ws-muted)">${escape_html(r.why)}</p> <div class="flex flex-wrap gap-2 text-xs font-mono"><span style="color:var(--ws-accent2)">📅 ${escape_html(r.best_time)}</span> <span style="color:var(--ws-green)">💶 ${escape_html(r.estimated_budget)}</span> <span style="color:var(--ws-text)">⭐ ${escape_html(r.highlight)}</span></div></div>`);
      }
      $$renderer2.push(`<!--]--></div>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  var $$store_subs;
  if (store_get($$store_subs ??= {}, "$currentPage", currentPage) === "home") {
    $$renderer.push("<!--[0-->");
    Dashboard($$renderer);
  } else if (store_get($$store_subs ??= {}, "$currentPage", currentPage) === "priceradar") {
    $$renderer.push("<!--[1-->");
    PriceRadar($$renderer);
  } else if (store_get($$store_subs ??= {}, "$currentPage", currentPage) === "mytrips") {
    $$renderer.push("<!--[2-->");
    MyTrips($$renderer);
  } else if (store_get($$store_subs ??= {}, "$currentPage", currentPage) === "discover") {
    $$renderer.push("<!--[3-->");
    Discover($$renderer);
  } else {
    $$renderer.push("<!--[-1-->");
  }
  $$renderer.push(`<!--]-->`);
  if ($$store_subs) unsubscribe_stores($$store_subs);
}
export {
  _page as default
};
