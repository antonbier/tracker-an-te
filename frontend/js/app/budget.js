// frontend/js/app/budget.js
import { api } from '../core/api.js';
import { t } from '../ui/i18n.js';
import { toast } from '../ui/toast.js';
import { API_URL, trips, setTrips } from '../core/state.js';

export let allExpenses = [];

export function toggleActualSync(on) {
  document.getElementById('manualEntry').style.display = on ? 'none' : 'block';
  document.getElementById('actualEntry').style.display = on ? 'block' : 'none';
  if (on && (!localStorage.getItem('s-actualUrl') || !localStorage.getItem('s-actualFile'))) {
    document.getElementById('actualNotice').style.display = 'block';
  } else {
    document.getElementById('actualNotice').style.display = 'none';
  }
}

export function addTrip() {
  const name = document.getElementById('tripName').value.trim();
  const cost = parseFloat(document.getElementById('tripCost').value);
  if (!name || isNaN(cost) || cost <= 0) { toast(t('error') + ': ' + t('budgetTripName'), 'error'); return; }
  trips.push({ name, cost, date: new Date().toISOString().slice(0,10) });
  setTrips([...trips]);
  document.getElementById('tripName').value = '';
  document.getElementById('tripCost').value = '';
  renderBudget();
}

export async function syncActualBudget() {
  const url      = localStorage.getItem('s-actualUrl')      || '';
  const password = localStorage.getItem('s-actualPassword') || '';
  const file     = localStorage.getItem('s-actualFile')     || '';
  if (!url || !password || !file) {
    document.getElementById('actualNotice').style.display = 'block';
    toast(t('actualBudgetError') + ': ' + t('budgetNoActual'), 'warning');
    return;
  }
  toast(t('actualBudgetSyncing'), 'warning');
  const resultEl = document.getElementById('actualSyncResult');
  try {
    const resp = await fetch((localStorage.getItem('apiUrl')||API_URL) + '/api/budget/actual/summary', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ base_url: url, password, budget_file: file }),
    });
    const data = await resp.json();
    if (data.error) { toast(t('actualBudgetError') + ': ' + data.error, 'error'); return; }
    if (data.travel_categories && data.travel_categories.length) {
      setTrips(data.travel_categories.map(cat => ({ name: cat.name, cost: cat.spent, date: data.month, source: 'actualbudget' })));
    }
    resultEl.style.display = 'block';
    resultEl.innerHTML = `<div style="font-size:.72rem;color:var(--green)">
      ✓ ${t('actualBudgetSynced')} — ${data.month}<br>
      ${data.travel_categories?.length || 0} Reise-Kategorien | ${(data.total_spent||0).toFixed(2)} € ausgegeben
    </div>`;
    if ((data.total_budgeted||0) > 0) {
      document.getElementById('budgetTotal').value = data.total_budgeted.toFixed(2);
      localStorage.setItem('ws-budget', data.total_budgeted.toFixed(2));
    }
    renderBudget();
    toast(t('actualBudgetSynced'), 'success');
  } catch(e) { toast(t('actualBudgetError') + ': ' + e.message, 'error'); }
}

export function updateBudget() {
  localStorage.setItem('ws-budget', document.getElementById('budgetTotal').value);
  renderBudget();
}

export function renderBudget() {
  const total     = parseFloat(document.getElementById('budgetTotal').value) || 0;
  const used      = trips.reduce((s, tr) => s + tr.cost, 0);
  const remaining = Math.max(0, total - used);
  const pct       = total > 0 ? Math.min(100, (used / total) * 100) : 0;
  document.getElementById('progressFill').style.width      = pct + '%';
  document.getElementById('progressFill').style.background = pct > 85 ? 'var(--red)' : pct > 60 ? 'var(--accent2)' : 'var(--accent)';
  document.getElementById('budgetUsedLabel').textContent      = used.toFixed(2) + ' €';
  document.getElementById('budgetRemainingLabel').textContent = remaining.toFixed(2) + ' €';
  const list = document.getElementById('tripList');
  list.innerHTML = trips.length
    ? trips.slice().reverse().map((tr, i) => `
        <div class="trip-item">
          <div><div class="trip-item-name">${tr.name}</div><div style="font-size:.65rem;color:var(--sub)">${tr.date}</div></div>
          <div style="display:flex;align-items:center;gap:.5rem">
            <div class="trip-item-cost">${tr.cost.toFixed(2)} €</div>
            <button class="btn-sm btn-danger" onclick="removeTrip(${trips.length-1-i})">✕</button>
          </div>
        </div>`).join('')
    : `<div style="font-size:.76rem;color:var(--muted);padding:.5rem 0">${t('noTrackers').replace('Tracker','Reisen')}</div>`;
}

export function removeTrip(idx) {
  const updated = [...trips];
  updated.splice(idx, 1);
  setTrips(updated);
  renderBudget();
}

export async function loadExpenses() {
  const wrap  = document.getElementById('expense-table-wrap');
  const sumEl = document.getElementById('expense-summary');
  const filEl = document.getElementById('expense-filters');
  if (!API_URL) return;
  const actualUrl      = localStorage.getItem('s-actualUrl')       || '';
  const actualPassword = localStorage.getItem('s-actualPassword')  || '';
  const actualFile     = localStorage.getItem('s-actualFile')      || '';
  const categories     = localStorage.getItem('s-travelCategories')|| '';
  const yearSel        = document.getElementById('expense-year-filter');
  const year           = yearSel?.value ? parseInt(yearSel.value) : null;
  if (!actualUrl || !actualPassword || !actualFile) {
    wrap.innerHTML = `<div class="expense-loading">⚙ ActualBudget ${t('missingUrl')} — ${t('settings')} öffnen</div>`;
    return;
  }
  wrap.innerHTML = `<div class="expense-loading"><span class="spinner"></span> ${t('expenseSyncing')}</div>`;
  try {
    const result = await api('/api/budget/actual/expenses', {
      method: 'POST',
      body: JSON.stringify({
        base_url: actualUrl, password: actualPassword, budget_file: actualFile,
        category_names: categories.split(',').map(c => c.trim()).filter(Boolean), year,
      }),
    });
    allExpenses = result.transactions || [];
    document.getElementById('expense-total').textContent = (result.total_spent||0).toFixed(2) + ' €';
    document.getElementById('expense-year').textContent  = result.year || new Date().getFullYear();
    document.getElementById('expense-count').textContent = allExpenses.length;
    if (sumEl) sumEl.style.display = 'grid';
    const cats = [...new Set(allExpenses.map(tx => tx.category).filter(Boolean))].sort();
    document.getElementById('expense-cat-filter').innerHTML =
      `<option value="">${t('expenseCategory')} (${t('total')})</option>` +
      cats.map(c => `<option value="${c}">${c}</option>`).join('');
    if (filEl) filEl.style.display = 'flex';
    const years = [...new Set(allExpenses.map(tx => tx.date?.slice(0,4)).filter(Boolean))].sort().reverse();
    if (yearSel) yearSel.innerHTML = `<option value="">Dieses Jahr</option>` +
      years.map(y => `<option value="${y}"${year==y?'selected':''}>${y}</option>`).join('');
    renderExpenseTable(allExpenses);
  } catch(e) {
    wrap.innerHTML = `<div class="expense-loading">❌ ${e.message}</div>`;
    if (sumEl) sumEl.style.display = 'none';
  }
}

export function filterExpenses() {
  const search   = document.getElementById('expense-search')?.value.toLowerCase() || '';
  const cat      = document.getElementById('expense-cat-filter')?.value || '';
  const filtered = allExpenses.filter(tx =>
    (!search || (tx.payee||'').toLowerCase().includes(search) || (tx.notes||'').toLowerCase().includes(search)) &&
    (!cat    || tx.category === cat)
  );
  renderExpenseTable(filtered);
}

export function renderExpenseTable(expenses) {
  const wrap = document.getElementById('expense-table-wrap');
  if (!expenses.length) {
    wrap.innerHTML = `<div class="expense-loading" data-i18n="expenseNoData">${t('expenseNoData')}</div>`;
    return;
  }
  wrap.innerHTML = `<div class="expense-table-wrap"><table class="expense-table">
    <thead><tr>
      <th data-i18n="expenseDate">${t('expenseDate')}</th>
      <th data-i18n="expensePayee">${t('expensePayee')}</th>
      <th data-i18n="expenseCategory">${t('expenseCategory')}</th>
      <th data-i18n="expenseAmount" style="text-align:right">${t('expenseAmount')}</th>
    </tr></thead>
    <tbody>${expenses.map(tx => {
      const neg  = tx.amount < 0;
      const amt  = Math.abs(tx.amount).toFixed(2);
      return `<tr>
        <td>${tx.date||'–'}</td>
        <td>${tx.payee||'–'}<br><span style="font-size:.65rem;color:var(--sub)">${tx.notes||''}</span></td>
        <td><span class="badge badge-fallback" style="font-size:.6rem">${tx.category||'–'}</span></td>
        <td style="text-align:right"><span class="${neg?'expense-amount-neg':'expense-amount-pos'}">${neg?'−':'+'} ${amt} €</span></td>
      </tr>`;
    }).join('')}</tbody>
  </table></div>`;
}
