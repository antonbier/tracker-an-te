// frontend/js/core/state.js
// Zentraler, mutierbarer App-State – wird von allen Modulen importiert.

export let TRANSLATIONS     = {};
export let currentLang      = localStorage.getItem('lang') || 'de';
export let API_URL          = localStorage.getItem('apiUrl') || '';
export let selectedTrackerId = null;
export let priceChart       = null;
export let selectedBags     = new Set();
export let currentPage      = 'ryanair';
export let trips            = JSON.parse(localStorage.getItem('ws-trips') || '[]');
export let obStep           = 1;
export let allExpenses      = [];

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
