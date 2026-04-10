<script>
  let {
    telegramToken = $bindable(),
    telegramChat  = $bindable(),
    gotifyUrl     = $bindable(),
    gotifyToken   = $bindable(),
  } = $props();
</script>

<div class="space-y-2">
  <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Telegram</div>
  <div class="text-xs rounded-lg px-3 py-2" style="background:rgba(var(--ws-accent-rgb,211,95,57),.08);color:var(--ws-muted)">
    💡 <strong>Bot Token</strong>: Öffne <a href="https://t.me/BotFather" target="_blank" rel="noopener" style="color:var(--ws-accent)">@BotFather ↗</a> → /newbot → Token kopieren.<br/>
    <strong>Chat ID</strong>: Schreib dem Bot, dann <a href="https://api.telegram.org/bot{DEIN_TOKEN}/getUpdates" target="_blank" rel="noopener" style="color:var(--ws-accent)">getUpdates aufrufen ↗</a> und <code>chat.id</code> entnehmen.
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
  <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Gotify</div>
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
