/**
 * app/scratchmap.js — Scratch Map (SVG World Map)
 *
 * Renders an interactive SVG world map inside #scratch-map-container.
 * Visited countries (from Dawarich) are highlighted in var(--accent).
 *
 * Uses jsvectormap (CDN) with the world map projection. Falls back
 * to a simple country count display if the library fails to load.
 *
 * Functions exported:
 *   initScratchMap(visitedCodes)  — render map with highlighted countries
 *   loadScratchMap()              — fetch /api/dawarich/countries + init map
 */

import { API_URL } from '../core/state.js';
import { t } from '../ui/i18n.js';

// Track map instance so we can destroy/re-init on re-render
let _mapInstance = null;

/**
 * Initialize the scratch map with a list of visited ISO-2 country codes.
 * @param {string[]} visitedCodes  e.g. ['DE', 'IT', 'FR']
 * @param {string[]} countryNames  display names for the legend
 * @param {number}   tripCount     total detected trips
 * @param {boolean}  configured    whether Dawarich is set up
 */
export function initScratchMap(visitedCodes = [], countryNames = [], tripCount = 0, configured = true) {
  const container = document.getElementById('scratch-map-container');
  if (!container) return;

  // Build selected regions object for jsvectormap
  const selectedRegions = {};
  visitedCodes.forEach(code => { selectedRegions[code] = true; });

  // Destroy previous instance if exists
  if (_mapInstance) {
    try { _mapInstance.destroy(); } catch(e) {}
    _mapInstance = null;
  }
  container.innerHTML = '';

  // Not configured state
  if (!configured) {
    container.innerHTML = `
      <div class="scratch-map-unconfigured">
        <div class="scratch-map-unconfigured-icon">🗺️</div>
        <div class="scratch-map-unconfigured-title" data-i18n="scratchMapNotConfigured">Dawarich nicht verknüpft</div>
        <div class="scratch-map-unconfigured-desc" data-i18n="scratchMapDesc">Verbinde Dawarich in den Einstellungen, um deine besuchten Länder auf der Weltkarte zu sehen.</div>
        <button class="btn-primary" style="width:auto;margin-top:1rem;padding:.5rem 1.2rem"
                onclick="openSettings()" data-i18n="statSetupLink">Einrichten →</button>
      </div>`;
    return;
  }

  // Map wrapper
  const mapEl = document.createElement('div');
  mapEl.id = 'scratch-map-svg';
  mapEl.style.cssText = 'width:100%;height:340px;';
  container.appendChild(mapEl);

  // Legend
  const legend = document.createElement('div');
  legend.className = 'scratch-map-legend';
  const visitedLabel = visitedCodes.length
    ? `${visitedCodes.length} ${t('scratchMapCountries') || 'Länder'} · ${tripCount} ${t('tripNights') ? t('scratchMapTrips') || 'Reisen' : 'Reisen'}`
    : t('scratchMapNoVisits') || 'Noch keine besuchten Länder';
  legend.innerHTML = `
    <div class="scratch-map-legend-item">
      <span class="scratch-map-dot scratch-map-dot--visited"></span>
      <span>${t('scratchMapVisited') || 'Besucht'}</span>
    </div>
    <div class="scratch-map-legend-item">
      <span class="scratch-map-dot scratch-map-dot--unvisited"></span>
      <span>${t('scratchMapNotVisited') || 'Nicht besucht'}</span>
    </div>
    <div class="scratch-map-count">${visitedLabel}</div>
  `;
  container.appendChild(legend);

  // Init jsvectormap
  try {
    if (typeof jsVectorMap === 'undefined') throw new Error('jsvectormap not loaded');

    // Compute CSS variable values for theming
    const style = getComputedStyle(document.documentElement);
    const accent  = style.getPropertyValue('--accent').trim()  || '#D95D39';
    const surface2= style.getPropertyValue('--surface2').trim()|| '#f2f0ec';
    const border  = style.getPropertyValue('--border').trim()  || '#e2ddd6';
    const sub     = style.getPropertyValue('--sub').trim()     || '#7a7068';

    _mapInstance = new jsVectorMap({
      selector: '#scratch-map-svg',
      map: 'world',

      // Colours
      regionStyle: {
        initial: {
          fill:          surface2,
          stroke:        border,
          strokeWidth:   0.5,
          fillOpacity:   1,
        },
        hover: {
          fill:          accent,
          fillOpacity:   0.7,
          cursor:        'pointer',
        },
        selected: {
          fill: accent,
        },
        selectedHover: {
          fill: accent,
          fillOpacity: 0.85,
        },
      },

      // Background / ocean
      backgroundColor: 'transparent',

      // Pre-select visited countries
      selectedRegions: visitedCodes,

      // Tooltip
      showTooltip: true,
      tooltip: {
        style: {
          backgroundColor: 'var(--surface)',
          color:           'var(--text)',
          border:          '1px solid var(--border)',
          borderRadius:    '8px',
          padding:         '4px 10px',
          fontSize:        '12px',
          fontFamily:      'var(--sans)',
          boxShadow:       'var(--shadow-sm)',
        },
      },

      // Zoom controls
      zoomButtons: false,
      zoomOnScroll: false,
    });
  } catch(e) {
    // Fallback: simple country list if jsvectormap fails
    console.warn('[ScratchMap] jsvectormap not available, using fallback:', e.message);
    _renderFallback(container, visitedCodes, countryNames, tripCount);
  }
}

/** Fallback renderer — simple grid of country badges */
function _renderFallback(container, codes, names, tripCount) {
  container.innerHTML = `
    <div class="scratch-map-fallback">
      <div class="scratch-map-fallback-header">
        <span class="scratch-map-fallback-count">${codes.length}</span>
        <span>${t('scratchMapCountries') || 'besuchte Länder'}</span>
        <span class="scratch-map-fallback-trips">· ${tripCount} ${t('scratchMapTrips') || 'Reisen'}</span>
      </div>
      <div class="scratch-map-badges">
        ${codes.map((code, i) => `
          <div class="scratch-map-badge" title="${names[i] || code}">
            <span class="scratch-map-flag">${_codeToFlag(code)}</span>
            <span>${code}</span>
          </div>`).join('')}
        ${codes.length === 0 ? `<div class="scratch-map-empty">${t('scratchMapNoVisits') || 'Noch keine besuchten Länder'}</div>` : ''}
      </div>
    </div>`;
}

/** Convert ISO-2 code to flag emoji */
function _codeToFlag(code) {
  return code.toUpperCase().replace(/./g, c =>
    String.fromCodePoint(c.charCodeAt(0) + 127397)
  );
}

/**
 * Fetch visited countries from backend and initialize the map.
 * Shows a loading state while fetching.
 */
export async function loadScratchMap() {
  const container = document.getElementById('scratch-map-container');
  if (!container) return;

  // Loading state
  container.innerHTML = `<div class="scratch-map-loading"><span class="spinner"></span> <span data-i18n="scratchMapLoading">Lade Karte…</span></div>`;

  if (!API_URL) {
    initScratchMap([], [], 0, false);
    return;
  }

  try {
    const resp = await fetch(API_URL + '/api/dawarich/countries');
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    initScratchMap(
      data.country_codes || [],
      data.countries     || [],
      data.trip_count    || 0,
      data.configured    !== false
    );
  } catch(e) {
    console.warn('[ScratchMap] fetch failed:', e.message);
    // Try to read from locally cached trips
    initScratchMap([], [], 0, false);
  }
}
