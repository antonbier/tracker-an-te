/**
 * core/state.js — Central mutable application state
 *
 * All global variables live here and are exported as named exports.
 * Modules that need to READ state import the variable directly.
 * Modules that need to WRITE state call the corresponding setter function,
 * because ES Module live bindings don't allow external reassignment.
 *
 * Example:
 *   import { API_URL, setApiUrl } from '../core/state.js';
 *   setApiUrl('http://192.168.1.51:8766');   // correct
 *   API_URL = '...';                          // won't work across module boundary
 */

export let TRANSLATIONS     = {};  // { 'de': {...}, 'en': {...}, 'it': {...} }
export let currentLang      = localStorage.getItem('lang') || 'de';
export let API_URL          = localStorage.getItem('apiUrl') || '';
export let selectedTrackerId = null;  // ID of the currently selected Ryanair tracker
export let priceChart       = null;   // Active Chart.js instance (destroyed on re-render)
export let selectedBags     = new Set(); // Baggage types selected in the add-tracker form
export let currentPage      = 'ryanair';
export let trips            = JSON.parse(localStorage.getItem('ws-trips') || '[]');
export let obStep           = 1;     // Onboarding wizard step (1-3)
export let allExpenses      = [];    // Cached ActualBudget transactions

export function setTranslations(val)        { TRANSLATIONS = val; }
export function setCurrentLang(val)         { currentLang = val; localStorage.setItem('lang', val); }
export function setApiUrl(val)              { API_URL = val; }
export function setSelectedTrackerId(val)   { selectedTrackerId = val; }
export function setPriceChart(val)          { priceChart = val; }
export function setSelectedBags(val)        { selectedBags = val; }
export function setCurrentPage(val)         { currentPage = val; }
export function setTrips(val)               { trips = val; localStorage.setItem('ws-trips', JSON.stringify(val)); }
export function setObStep(val)              { obStep = val; }
export function setAllExpenses(val)         { allExpenses = val; }
