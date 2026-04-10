<script>
  let {
    openaiKey = $bindable(),
    geminiKey = $bindable(),
  } = $props();
</script>

<div class="space-y-3 mt-1">
  <div class="space-y-2">
    <div class="text-xs font-semibold" style="color:var(--ws-text)">OpenAI</div>
    <div class="text-xs" style="color:var(--ws-muted)">KI-Reiseempfehlungen &amp; smarte Zusammenfassungen</div>
    <input bind:value={openaiKey} type="password" placeholder="OpenAI Key (sk-…)"
      class="w-full px-3 py-2 rounded-xl border text-sm"
      style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
    <div class="text-xs" style="color:var(--ws-muted)">
      Key: <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener" style="color:var(--ws-accent)">platform.openai.com ↗</a>
    </div>
  </div>
  <div class="space-y-2">
    <div class="text-xs font-semibold" style="color:var(--ws-text)">Google Gemini</div>
    <div class="text-xs" style="color:var(--ws-muted)">Alternative KI-Engine</div>
    <input bind:value={geminiKey} type="password" placeholder="Gemini Key (AIzaSy…)"
      class="w-full px-3 py-2 rounded-xl border text-sm"
      style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
    <div class="text-xs" style="color:var(--ws-muted)">
      Key: <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener" style="color:var(--ws-accent)">aistudio.google.com ↗</a>
    </div>
  </div>
</div>
