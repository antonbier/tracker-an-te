<script>
  import { api } from '$lib/api.js';
  import { toast } from '$lib/toast.js';

  let {
    telegramToken = $bindable(),
    telegramChat  = $bindable(),
    gotifyUrl     = $bindable(),
    gotifyToken   = $bindable(),
  } = $props();

  let telegramTesting = $state(false);
  let gotifyTesting   = $state(false);

  async function testTelegram() {
    telegramTesting = true;
    try {
      const res = await api('/api/notifications/test-telegram', { method: 'POST' });
      if (res?.success) toast('✅ Telegram-Testnachricht gesendet!', 'success');
      else toast('❌ ' + (res?.message || 'Fehler — Token und Chat-ID prüfen'), 'error');
    } catch (e) { toast('❌ ' + (e.message || 'Verbindungsfehler'), 'error'); }
    telegramTesting = false;
  }

  async function testGotify() {
    gotifyTesting = true;
    try {
      const res = await api('/api/notifications/test-gotify', { method: 'POST' });
      if (res?.success) toast('✅ Gotify-Testnachricht gesendet!', 'success');
      else toast('❌ ' + (res?.message || 'Fehler — URL und App-Token prüfen'), 'error');
    } catch (e) { toast('❌ ' + (e.message || 'Verbindungsfehler'), 'error'); }
    gotifyTesting = false;
  }
</script>

<div class="space-y-2">
  <div class="flex items-center justify-between">
    <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Telegram</div>
    <button
      onclick={testTelegram}
      disabled={telegramTesting || !telegramToken || !telegramChat}
      class="text-xs px-3 py-1 rounded-lg font-semibold transition-opacity disabled:opacity-40 hover:opacity-80"
      style="background:rgba(37,99,235,.12);color:#2563eb;border:1px solid rgba(37,99,235,.2)">
      {telegramTesting ? '⏳ Sende…' : '🚀 Testnachricht'}
    </button>
  </div>
  <div class="text-xs rounded-lg px-3 py-2" style="background:rgba(var(--ws-accent-rgb,211,95,57),.08);color:var(--ws-muted)">
    💡 <strong>Bot Token</strong>: Öffne <a href="https://t.me/BotFather" target="_blank" rel="noopener" style="color:var(--ws-accent)">@BotFather ↗</a> → /newbot → Token kopieren.<br/>
    <strong>Chat ID</strong>: Schreib dem Bot, dann <a href="https://api.telegram.org/bot<BOT_TOKEN>/getUpdates" target="_blank" rel="noopener" style="color:var(--ws-accent)">getUpdates aufrufen ↗</a> und <code>chat.id</code> entnehmen.<br/>
    💡 <strong>Tipp</strong>: Sende eine Nachricht an <a href="https://t.me/userinfobot" target="_blank" rel="noopener" style="color:var(--ws-accent)">@userinfobot ↗</a> — der Bot antwortet direkt mit deiner Chat-ID.
  </div>
  <input bind:value={telegramToken} type="password" placeholder="Bot Token (von @BotFather)"
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
  <input bind:value={telegramChat} placeholder="Chat ID (z.B. 123456789)"
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
</div>

<hr style="border-color:var(--ws-border)"/>

<div class="space-y-2">
  <div class="flex items-center justify-between">
    <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Gotify</div>
    <button
      onclick={testGotify}
      disabled={gotifyTesting || !gotifyUrl || !gotifyToken}
      class="text-xs px-3 py-1 rounded-lg font-semibold transition-opacity disabled:opacity-40 hover:opacity-80"
      style="background:rgba(22,163,74,.12);color:var(--ws-green);border:1px solid rgba(22,163,74,.2)">
      {gotifyTesting ? '⏳ Sende…' : '🚀 Testnachricht'}
    </button>
  </div>
  <div class="text-xs rounded-lg px-3 py-2" style="background:rgba(var(--ws-accent-rgb,211,95,57),.08);color:var(--ws-muted)">
    💡 <strong>App Token</strong>: Gotify öffnen → Apps → Neue App anlegen → Token aus App-Details kopieren.
  </div>
  <input bind:value={gotifyUrl} placeholder="https://gotify.example.com"
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
  <input bind:value={gotifyToken} type="password" placeholder="App Token (aus Gotify Apps)"
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
</div>
