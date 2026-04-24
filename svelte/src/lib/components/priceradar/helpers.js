// ── PriceRadar Helpers ────────────────────────────────────────────────────
// Pure functions only — no $state, no imports from Svelte, no side effects.
// Functions that need the i18n `t` store accept it as a parameter.

// ── Date helpers ──────────────────────────────────────────────────────────

/** Returns today + offset days as YYYY-MM-DD */
export function dateOffset(days) {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

/** Formats YYYY-MM-DD to the user's configured date format (from localStorage) */
export function fmtDate(iso) {
  if (!iso) return '–';
  const parts = String(iso).slice(0, 10).split('-');
  if (parts.length !== 3) return iso;
  const [yyyy, mm, dd] = parts;
  const fmt = typeof localStorage !== 'undefined'
    ? (localStorage.getItem('ws-date-format') || 'DD.MM.YYYY')
    : 'DD.MM.YYYY';
  if (fmt === 'MM/DD/YYYY') return `${mm}/${dd}/${yyyy}`;
  if (fmt === 'YYYY-MM-DD') return `${yyyy}-${mm}-${dd}`;
  return `${dd}.${mm}.${yyyy}`;
}

/** Formats a date range using fmtDate */
export function fmtRange(from, to) {
  return to ? `${fmtDate(from)} – ${fmtDate(to)}` : fmtDate(from);
}

/** Returns overnight suffix like "(+1)" if flight crosses midnight */
export function overnightSuffix(depTime, arrTime, durationMin) {
  if (!depTime || !arrTime || !durationMin) return '';
  try {
    const [dh, dm] = String(depTime).slice(0, 5).split(':').map(Number);
    const days = Math.floor((dh * 60 + dm + durationMin) / 1440);
    return days > 0 ? `(+${days})` : '';
  } catch { return ''; }
}

// ── Chart helpers ─────────────────────────────────────────────────────────

/** Computes SVG polyline + area + min/max points for a price history array */
export function chartPts(history, w = 290, h = 65, pad = 5) {
  const prices = history.map(e => e.price);
  const minP   = Math.min(...prices);
  const maxP   = Math.max(...prices);
  const range  = maxP - minP || 1;
  const pts = history.map((e, i) => {
    const x = (i / (history.length - 1 || 1)) * w + pad;
    const y = h - ((e.price - minP) / range) * (h - 5);
    // date: prefer fetched_at, fall back to created_at
    const raw = e.fetched_at || e.created_at || '';
    const date = raw.slice(0, 10);
    return { x, y, price: e.price, date };
  });
  const minPt = pts.reduce((m, p) => p.price < m.price ? p : m, pts[0]);
  const maxPt = pts.reduce((m, p) => p.price > m.price ? p : m, pts[0]);
  return {
    minP, maxP,
    minPt, maxPt,
    pts,   // ← neu: alle Punkte inkl. date für Tooltip
    polyline: pts.map(p => `${p.x},${p.y}`).join(' '),
    area: [
      `${pad},${h}`,
      ...pts.map(p => `${p.x},${p.y}`),
      `${(history.length > 1 ? 1 : 0) * w + pad},${h}`,
    ].join(' '),
  };
}

/** Returns { dir: 'up'|'down'|'equal', pct: string } from last 2 history entries */
export function priceTrend(history) {
  if (!history || history.length < 2) return null;
  const last = history[history.length - 1].price;
  const prev = history[history.length - 2].price;
  if (last < prev) return { dir: 'down', pct: (((prev - last) / prev) * 100).toFixed(1) };
  if (last > prev) return { dir: 'up',   pct: (((last - prev) / prev) * 100).toFixed(1) };
  return { dir: 'equal', pct: '0.0' };
}

/** Returns true if current price is at or below historical minimum */
export function isTopPrice(history, currentPrice) {
  if (!history || history.length < 2 || currentPrice == null) return false;
  const minHist = Math.min(...history.map(e => e.price));
  return currentPrice <= minHist;
}

// ── Layover helper ────────────────────────────────────────────────────────

/** Formats layover duration in minutes to "Xh Ym" */
export function fmtLayoverDur(minutes) {
  if (!minutes || minutes <= 0) return '';
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h > 0 ? (m > 0 ? `${h}h ${m}m` : `${h}h`) : `${m}m`;
}

/** Safely parses a JSON field that may be a string, array, or null */
export function parseJsonField(val) {
  if (!val) return [];
  if (Array.isArray(val)) return val;
  try { return JSON.parse(val) || []; } catch { return []; }
}

// ── Tracker label helpers ─────────────────────────────────────────────────

/** Returns display title for a tracker card */
export function trackerTitle(tr) {
  if (tr._type === 'flight' || tr._type === 'google_flight') {
    return `${tr.origin} → ${tr.destination}`;
  }
  if (tr._type === 'hotel')   return `🏨 ${tr.hotel_name || tr.destination}`;
  if (tr._type === 'camping') return `⛺ ${tr.campsite_name || tr.region || tr.destination || ''}`;
  return tr.destination || tr.location_name || '–';
}

/** Returns subtitle line for a tracker card (dates, pax, rooms).
 *  @param {object} tr  — tracker object
 *  @param {function} tFn — the resolved t() function (get(t) from caller)
 */
export function trackerSubtitle(tr, tFn) {
  const parts = [];
  if (tr.outbound_date) parts.push(fmtDate(tr.outbound_date) + (tr.return_date ? ' ⇄ ' + fmtDate(tr.return_date) : ''));
  if (tr.checkin_date)  parts.push(fmtDate(tr.checkin_date)  + (tr.checkout_date ? ' – ' + fmtDate(tr.checkout_date) : ''));
  if (tr.adults) parts.push(tr.adults + ' ' + tFn('radarAdultsShort'));
  if (tr.rooms)  parts.push(tr.rooms  + ' Zi.');
  return parts.join(' · ');
}

/** Returns array of inclusion badge strings for a tracker card.
 *  @param {object} tr  — tracker object
 *  @param {function} tFn — the resolved t() function (get(t) from caller)
 */
export function trackerBadges(tr, tFn) {
  const badges = [];
  if (tr._type === 'flight') {
    try {
      const bagItems = JSON.parse(tr.baggage_json || '[]');
      const cnt10 = bagItems.filter(b => b.type === '10kg').length;
      const cnt20 = bagItems.filter(b => b.type === '20kg').length;
      const cnt23 = bagItems.filter(b => b.type === '23kg').length;
      if (cnt10 > 0) badges.push(`🎒 ${cnt10}× 10kg`);
      if (cnt20 > 0) badges.push(`🎒 ${cnt20}× 20kg`);
      if (cnt23 > 0) badges.push(`🧳 ${cnt23}× 23kg`);
    } catch {}
    if ((tr.seat_cost || 0) > 0) badges.push(tFn('radarSeatBadge').replace('{n}', tr.seat_cost));
  }
  if (tr._type === 'google_flight') {
    try {
      const bg = JSON.parse(tr.baggage_json || '{}');
      if (bg.baggage_10kg > 0) badges.push(`🎒 ${bg.baggage_10kg}× 10kg`);
      else if (bg.baggage === '10kg') badges.push('🎒 1× 10kg');
      if (bg.baggage_20kg > 0) badges.push(`🎒 ${bg.baggage_20kg}× 20kg`);
      else if (bg.baggage === '20kg' && !bg.baggage_10kg) badges.push('🎒 1× 20kg');
      if (bg.baggage_23kg > 0) badges.push(`🧳 ${bg.baggage_23kg}× 23kg`);
    } catch {}
    if ((tr.seat_cost || 0) > 0) badges.push(tFn('radarSeatBadge').replace('{n}', tr.seat_cost));
  }
  if (tr._type === 'camping') {
    const at = (tr.accommodation_type || '').toLowerCase();
    if (at.includes('mobilheim') || at.includes('chalet')) badges.push('⛺ Mobilheim');
    else if (at.includes('glamping')) badges.push('🌟 Glamping');
    else if (at.includes('stellplatz') || at.includes('pitch')) badges.push('🅿️ Stellplatz');
    if (tr.aircon) badges.push('❄️ Klima');
    if (tr.pets)   badges.push('🐕 Hunde');
  }
  if (tr._type === 'hotel') {
    if (tr.rooms > 1) badges.push(`🛏 ${tr.rooms} Zi.`);
  }
  return badges;
}

/** Returns emoji icon for a tracker type */
export function providerIcon(type) {
  if (type === 'flight')        return '🟠';
  if (type === 'google_flight') return '🔵';
  if (type === 'camping')       return '⛺';
  if (type === 'hotel')         return '🏨';
  return '📍';
}

/** Returns human-readable provider name for a tracker */
export function providerLabel(tr) {
  if (tr._type === 'flight')        return 'Ryanair';
  if (tr._type === 'google_flight') return 'Google Flights';
  if (tr._type === 'hotel')         return tr.source === 'google_hotels' ? 'Google Hotels' : 'Booking.com';
  if (tr._type === 'camping')       return 'Homair';
  return tr._type;
}

/** Computes a booking deep-link for a tracker, falling back to constructed URLs */
export function trackerBookingUrl(tr) {
  if (tr.booking_url) return tr.booking_url;
  if (tr._type === 'flight') {
    const o = tr.origin, d = tr.destination, dt = tr.outbound_date, ret = tr.return_date || '';
    const adults = tr.adults || 1, children = tr.children || 0, isReturn = ret ? 'true' : 'false';
    return 'https://www.ryanair.com/de/de/trip/flights/select'
      + '?adults=' + adults + '&teens=0&children=' + children + '&infants=0'
      + '&dateOut=' + dt + '&dateIn=' + ret + '&isConnectedFlight=false&isReturn=' + isReturn
      + '&originIata=' + o + '&destinationIata=' + d
      + '&tpAdults=' + adults + '&tpTeens=0&tpChildren=' + children + '&tpInfants=0'
      + '&tpStartDate=' + dt + '&tpEndDate=' + ret + '&tpDiscount=0&tpPromoCode='
      + '&tpOriginIata=' + o + '&tpDestinationIata=' + d;
  }
  if (tr._type === 'google_flight')
    return 'https://www.google.com/flights#search;f=' + tr.origin + ';t=' + tr.destination + ';d=' + tr.outbound_date;
  if (tr._type === 'hotel')
    return 'https://www.google.com/travel/hotels?q=' + encodeURIComponent(tr.hotel_name || tr.destination || '') + '&dates=' + (tr.checkin_date || '') + '/' + (tr.checkout_date || '');
  if (tr._type === 'camping')
    return 'https://www.homair.com/';
  return null;
}
