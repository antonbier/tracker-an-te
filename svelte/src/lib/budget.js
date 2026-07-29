import { api } from '$lib/api.js';

/**
 * Shared jahresbudget Load/Save-Logik — genutzt von Dashboard.svelte
 * (currentYear) und MyTrips.svelte (selectedYear), die sonst identischen
 * Fetch/PUT-Code dupliziert hatten.
 */

export async function fetchBudgetByYear() {
  return (await api('/api/trips/budget')) || {};
}

export async function saveBudgetForYear(year, amount) {
  await api('/api/trips/budget', {
    method: 'PUT',
    body: JSON.stringify({ year, amount }),
  });
}
