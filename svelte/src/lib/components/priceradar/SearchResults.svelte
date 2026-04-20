<script>
  import { t } from '$lib/i18n.js';
  import { overnightSuffix, parseJsonField, fmtLayoverDur } from './helpers.js';

  const { searching, results, savingTracker, onsavetracker } = $props();

  let activeProviderFilter = $state('all');
  let savedTrackers = $state(new Set()); // IDs of recently saved trackers
  let stopsOpen = $state({}); // result.id → bool

  function handleSave(result) {
    onsavetracker(result);
    // Show '✓ Gespeichert' for 2s after clicking
    setTimeout(() => {
      savedTrackers = new Set([...savedTrackers, result.id]);
      setTimeout(() => {
        const next = new Set(savedTrackers);
        next.delete(result.id);
        savedTrackers = next;
      }, 2000);
    }, 100);
  }

  const providerChips = $derived(() => {
    return ['all', ...new Set(results.map(r => r.provider))];
  });

  const filteredResults = $derived(() => {
    if (activeProviderFilter === 'all') return results;
    return results.filter(r => r.provider === activeProviderFilter);
  });
</script>

{#if searching}
  <!-- Skeleton screens -->
  <div class="space-y-3">
    <div class="text-xs font-semibold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('radarSearchResults')}</div>
    {#each [1,2,3] as _}
      <div class="rounded-xl p-4 border animate-pulse" style="background:var(--ws-surface);border-color:var(--ws-border)">
        <div class="flex justify-between items-start">
          <div class="space-y-2 flex-1">
            <div class="h-4 w-40 rounded" style="background:var(--ws-border)"></div>
            <div class="h-3 w-56 rounded" style="background:var(--ws-border)"></div>
            <div class="flex gap-2">
              <div class="h-5 w-16 rounded-full" style="background:var(--ws-border)"></div>
              <div class="h-5 w-20 rounded-full" style="background:var(--ws-border)"></div>
            </div>
          </div>
          <div class="space-y-2 text-right">
            <div class="h-6 w-20 rounded" style="background:var(--ws-border)"></div>
            <div class="h-7 w-28 rounded-xl" style="background:var(--ws-border)"></div>
          </div>
        </div>
      </div>
    {/each}
  </div>

{:else if results.length > 0}
  <div class="space-y-3">
    <!-- Header + provider chips -->
    <div class="flex items-center gap-2 flex-wrap">
      <span class="text-xs font-semibold uppercase tracking-wider" style="color:var(--ws-muted)">
        {$t('radarSearchResults')} ({filteredResults().length})
      </span>
      <div class="flex gap-1.5 overflow-x-auto">
        {#each providerChips() as chip}
          <button
            onclick={() => activeProviderFilter = chip}
            class="px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap shrink-0 border transition-colors"
            style={activeProviderFilter === chip
              ? 'background:var(--ws-accent);color:#fff;border-color:var(--ws-accent)'
              : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)'}>
            {chip === 'all' ? $t('radarAllProviders') : chip}
          </button>
        {/each}
      </div>
    </div>

    <!-- Result cards -->
    {#each filteredResults() as result}
      {@const d = result.detail || {}}
      <div class="rounded-xl p-4 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
        <div class="flex items-start justify-between gap-2">
          <div class="flex-1 min-w-0 overflow-hidden">
            <div class="font-bold text-sm truncate" style="color:var(--ws-text)" title={result.title || result.label || ''}>{result.title || result.label || '–'}</div>
            {#if result.subtitle}
              {@const cleanSubtitle = d.airline
                ? result.subtitle
                    .replace(/·\s*[^·]+·\s*\d{2}:\d{2}→\d{2}:\d{2}/, '')
                    .replace(/(\d{4})-(\d{2})-(\d{2})/g, (_, y, m, d2) => `${d2}.${m}.${y}`)
                    .replace(/·\s*·/g, '·').trim().replace(/·\s*$/, '').trim()
                : result.subtitle.replace(/(\d{4})-(\d{2})-(\d{2})/g, (_, y, m, d2) => `${d2}.${m}.${y}`)}
              <div class="text-xs mt-0.5" style="color:var(--ws-muted)">{cleanSubtitle}</div>
            {/if}
            <!-- Airline + Flugzeiten -->
            {#if d.airline || (d.departure_time && d.arrival_time)}
              <div class="flex items-center gap-1.5 mt-1.5 flex-wrap">
                {#if d.airline}
                  <span class="text-xs">✈️</span>
                  <span class="text-xs font-semibold" style="color:var(--ws-accent)">{d.airline}</span>
                {/if}
                {#if d.flight_number}
                  <span class="text-xs font-mono px-1.5 py-0.5 rounded" style="background:var(--ws-surface2);color:var(--ws-muted)">{d.flight_number}</span>
                {/if}
                {#if d.departure_time && d.arrival_time}
                  {@const onSfx = overnightSuffix(d.departure_time, d.arrival_time, d.duration_min)}
                  <span class="text-xs font-mono" style="color:var(--ws-muted)">{String(d.departure_time).slice(0,5)} → {String(d.arrival_time).slice(0,5)}{onSfx ? ' ' + onSfx : ''}</span>
                {/if}
                {#if d.duration_min}
                  <span class="text-xs" style="color:var(--ws-muted)">({Math.floor(d.duration_min/60)}h{String(d.duration_min%60).padStart(2,'0')}m)</span>
                {:else if d.departure_time && d.arrival_time}
                  {@const _dh = parseInt(d.departure_time.slice(0,2)), _dm = parseInt(d.departure_time.slice(3,5))}
                  {@const _ah = parseInt(d.arrival_time.slice(0,2)),   _am = parseInt(d.arrival_time.slice(3,5))}
                  {@const _dur = (_ah*60+_am - (_dh*60+_dm) + 1440) % 1440}
                  {#if _dur > 0}
                    <span class="text-xs" style="color:var(--ws-muted)">({Math.floor(_dur/60)}h{String(_dur%60).padStart(2,'0')}m)</span>
                  {/if}
                {/if}
              </div>
            {/if}
            <!-- Stops dropdown (flights) -->
            {#if d.stops > 0 || (d.layover_airports && d.layover_airports !== '[]')}
              {@const stopKey = result.id}
              {@const layAirports  = parseJsonField(d.layover_airports)}
              {@const layDurations = parseJsonField(d.layover_durations)}
              <div class="mt-1.5">
                <button onclick={() => stopsOpen[stopKey] = !stopsOpen[stopKey]}
                  class="text-xs px-2 py-0.5 rounded-full font-semibold border transition-colors"
                  style="background:rgba(234,179,8,.1);border-color:rgba(234,179,8,.3);color:#ca8a04">
                  {d.stops ?? layAirports.length} Stopp{(d.stops ?? layAirports.length) > 1 ? 's' : ''} {stopsOpen[stopKey] ? '▴' : '▾'}
                </button>
                {#if stopsOpen[stopKey] && layAirports.length > 0}
                  <div class="mt-1 space-y-0.5 pl-2 border-l-2" style="border-color:var(--ws-border)">
                    {#each layAirports as ap, idx}
                      <div class="text-[10px]" style="color:var(--ws-muted)">
                        📍 {ap}{layDurations[idx] ? ' · ' + fmtLayoverDur(layDurations[idx]) : ''}
                      </div>
                    {/each}
                  </div>
                {/if}
              </div>
            {:else if d.stops === 0}
              <span class="text-xs px-2 py-0.5 rounded-full mt-1.5 inline-block"
                style="background:rgba(22,163,74,.1);color:var(--ws-green)">Nonstop</span>
            {/if}
            <div class="flex gap-1.5 flex-wrap mt-1.5">
              <span class="text-xs px-2 py-0.5 rounded-full"
                style="background:{result._test_mode ? 'rgba(234,179,8,.15)' : 'var(--ws-surface2)'};color:{result._test_mode ? '#ca8a04' : 'var(--ws-muted)'}">
                {result.provider}
              </span>
              {#each (result.badges || []) as badge}
                <span class="text-xs px-2 py-0.5 rounded-full" style="background:rgba(196,98,45,.08);color:var(--ws-accent)">{badge}</span>
              {/each}
            </div>
          </div>
          <div class="text-right flex-none pl-1" style="min-width:90px;max-width:130px">
            <div class="font-bold font-mono text-base whitespace-nowrap" style="color:var(--ws-green)">
              {result.price ? result.price.toFixed(2) + ' €' : '–'}
            </div>
            {#if result.price_per_night && result.nights > 1}
              <div class="text-[10px] font-mono whitespace-nowrap" style="color:var(--ws-muted)">
                Ø {result.price_per_night.toFixed(2)} {$t('radarPerNight')}
              </div>
            {/if}
            <button
              onclick={() => handleSave(result)}
              disabled={savingTracker === result.id || savedTrackers.has(result.id) || result._test_mode}
              title={result._test_mode ? 'Testpreise können nicht gespeichert werden' : ''}
              class="mt-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all hover:opacity-80 disabled:opacity-50"
              style="background:{savedTrackers.has(result.id) ? 'rgba(45,106,79,.15)' : result._test_mode ? 'var(--ws-surface2)' : 'linear-gradient(135deg,var(--ws-accent),#b84928)'};color:{savedTrackers.has(result.id) ? 'var(--ws-green)' : result._test_mode ? 'var(--ws-muted)' : '#fff5ec'};border:1px solid {savedTrackers.has(result.id) ? 'var(--ws-green)' : result._test_mode ? 'var(--ws-border)' : 'transparent'}">
              {result._test_mode ? '🧪 Nur Test' : savedTrackers.has(result.id) ? '✓ Gespeichert' : savingTracker === result.id ? '⏳…' : $t('radarSaveTracker')}
            </button>
            {#if result.booking_url}
              <a href={result.booking_url} target="_blank" rel="noopener noreferrer"
                class="mt-1 block text-center px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all hover:opacity-80"
                style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-accent);text-decoration:none">
                Buchen ↗
              </a>
            {/if}
          </div>
        </div>
      </div>
    {/each}
  </div>
{/if}
