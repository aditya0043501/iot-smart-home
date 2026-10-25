/**
 * AETHER — AI Service Bridge (Frontend ↔ AI Service)
 * ---------------------------------------------------
 * Loaded AFTER app.js. Connects the frontend to the AI service
 * running on port 8089. Gracefully no-ops if the service is down.
 *
 * Responsibilities:
 *   - Poll /health every 10 s to detect service state
 *   - Push current device states to /api/readings every 15 s
 *   - Fetch anomaly events and render alert banners
 *   - Fetch energy forecast and render on AI Insights view
 *   - Expose window.AIBridge.renderInsights() for app.js
 */

(function () {
  'use strict';

  const AI_BASE = 'http://localhost:8089';
  const POLL_INTERVAL_MS  = 10_000;   // health check
  const PUSH_INTERVAL_MS  = 15_000;   // push device state
  const ALERT_INTERVAL_MS = 20_000;   // fetch anomalies

  let _aiOnline   = false;
  let _lastStatus = null;

  // ── Safe fetch (never throws to the caller) ────────────────
  async function apiFetch(path, opts = {}) {
    try {
      const res = await fetch(AI_BASE + path, {
        ...opts,
        headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      return null;   // service down or CORS blocked
    }
  }

  // ── Health polling ─────────────────────────────────────────
  async function pollHealth() {
    const data = await apiFetch('/health');
    const wasOnline = _aiOnline;
    _aiOnline = !!data;
    _lastStatus = data;

    updateAIStatusBadge(data);

    if (!wasOnline && _aiOnline) {
      showToast('🤖 AI Service connected — machine learning active', 'success');
    } else if (wasOnline && !_aiOnline) {
      showToast('⚠️ AI Service offline — running in standalone mode', 'warning');
    }
  }

  // ── Push device state to AI service ───────────────────────
  async function pushDeviceStates() {
    if (!_aiOnline || !window.store) return;
    const devices = store.getDevices();
    const SPEED_MAP = { off: 0, low: 1, medium: 2, high: 3 };

    for (const dev of devices) {
      const payload = {
        device_id:    dev.id,
        device_name:  dev.name,
        device_type:  dev.type,
        room:         dev.room,
        state:        dev.state ? 1 : 0,
        power_watts:  dev.state ? (dev.power || 0) : 0,
        brightness:   dev.brightness   || null,
        temperature:  dev.currentTemp  || null,
        target_temp:  dev.targetTemp   || null,
        humidity:     dev.humidity     || null,
        battery_pct:  dev.battery      || null,
        is_locked:    dev.locked != null ? (dev.locked ? 1 : 0) : null,
        fan_speed_num: dev.speed ? (SPEED_MAP[dev.speed] ?? null) : null,
        is_recording:  dev.recording != null ? (dev.recording ? 1 : 0) : null,
        motion_detected: dev.motionDetected != null ? (dev.motionDetected ? 1 : 0) : null,
      };
      await apiFetch('/api/readings', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    }
  }

  // ── Fetch & display anomaly alerts ────────────────────────
  async function fetchAndShowAnomalies() {
    if (!_aiOnline) return;
    const data = await apiFetch('/api/anomalies?limit=5');
    if (!data || !data.anomalies.length) return;

    const latest = data.anomalies[0];
    if (latest.acknowledged) return;

    // Render toast for new anomalies
    const badge = latest.score >= 0.8 ? '🚨' : '⚠️';
    const type  = latest.score >= 0.8 ? 'error' : 'warning';
    showToast(
      `${badge} <strong>${latest.algorithm}</strong>: ${latest.explanation?.slice(0, 80)}…`,
      type,
      8000
    );

    // Update anomaly panel in AI Insights view if visible
    renderAnomalyPanel(data.anomalies);
  }

  // ── AI Insights View Renderer ─────────────────────────────
  async function renderInsights() {
    const view = document.getElementById('view-ai');
    if (!view) return;

    if (!_aiOnline) {
      view.innerHTML = _offlinePlaceholder();
      return;
    }

    view.innerHTML = _insightsSkeleton();

    const [statusData, forecastData, anomalyData] = await Promise.all([
      apiFetch('/api/ai/status'),
      apiFetch('/api/forecast/energy'),
      apiFetch('/api/anomalies?limit=10'),
    ]);

    view.innerHTML = _buildInsightsHTML(statusData, forecastData, anomalyData);
    if (window.lucide) lucide.createIcons({ nodes: [view] });
    _attachInsightsListeners(view);

    // Render forecast chart if Chart.js is available
    if (forecastData && window.Chart) {
      _renderForecastChart(forecastData.forecast || []);
    }
  }

  function _offlinePlaceholder() {
    return `
    <div class="px-4 lg:px-8 py-8 max-w-7xl mx-auto">
      <div class="glass-card rounded-2xl p-12 flex flex-col items-center justify-center text-center gap-4">
        <div class="w-16 h-16 rounded-2xl bg-slate-500/20 text-slate-400 flex items-center justify-center">
          <i data-lucide="brain-circuit" class="w-8 h-8"></i>
        </div>
        <h3 class="font-bold text-xl text-slate-200">AI Service Offline</h3>
        <p class="text-sm text-slate-400 max-w-md">
          Start the AI service to enable machine learning features.
        </p>
        <code class="mt-2 px-4 py-2.5 rounded-xl bg-black/50 text-cyan-300 text-xs font-mono border border-white/10">
          python3 ai-service/main.py
        </code>
      </div>
    </div>`;
  }

  function _insightsSkeleton() {
    return `
    <div class="px-4 lg:px-8 py-8 max-w-7xl mx-auto space-y-6">
      ${[1,2,3].map(() => `<div class="glass-card rounded-2xl p-6 h-32 skeleton"></div>`).join('')}
    </div>`;
  }

  function _buildInsightsHTML(status, forecast, anomalies) {
    const s = status || {};
    const feats = s.features || {};
    const readingCount = s.reading_count || 0;
    const hoursData    = s.estimated_hours_of_data || 0;
    const modelsReady  = s.models_ready || false;

    const anomalyList = (anomalies?.anomalies || []).slice(0, 5);

    return `
    <div class="px-4 lg:px-8 py-8 max-w-7xl mx-auto space-y-8">

      <!-- Page Header -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-white/5">
        <div>
          <h2 class="text-2xl lg:text-3xl font-bold text-slate-100 flex items-center gap-3">
            <i data-lucide="brain-circuit" class="w-7 h-7 text-purple-400"></i>
            AI Insights
          </h2>
          <p class="text-xs sm:text-sm text-slate-400 mt-1">
            Real machine learning — ${readingCount.toLocaleString()} sensor readings collected · ${hoursData.toFixed(1)}h of data
          </p>
        </div>
        <div class="flex items-center gap-2 px-4 py-2 glass-panel rounded-xl text-xs">
          <span class="w-2 h-2 rounded-full ${modelsReady ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400 animate-ping'}"></span>
          <span class="font-mono ${modelsReady ? 'text-emerald-300' : 'text-amber-300'}">
            ${modelsReady ? 'Models Active' : 'Accumulating Data…'}
          </span>
        </div>
      </div>

      <!-- AI Status Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        ${_featureCard('zap', 'Energy Forecast', feats.energy_forecast, 'cyan')}
        ${_featureCard('shield-alert', 'Anomaly Detection', feats.anomaly_detection, 'rose')}
        ${_featureCard('users', 'Occupancy Model', feats.occupancy_model, 'purple')}
        ${_featureCard('message-square', 'LLM Control', feats.llm_control, 'blue')}
      </div>

      <!-- Demo Trigger Buttons -->
      <div class="glass-card p-6 rounded-2xl">
        <h3 class="font-bold text-base text-slate-100 mb-1 flex items-center gap-2">
          <i data-lucide="flask-conical" class="w-5 h-5 text-amber-400"></i>
          Demo Triggers
        </h3>
        <p class="text-xs text-slate-400 mb-5">Fire the AI pipeline with synthetic events to see it in action.</p>
        <div class="flex flex-wrap gap-3">
          <button id="demo-spike-btn" class="px-5 py-2.5 rounded-xl text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30 hover:bg-rose-500/30 transition-colors flex items-center gap-2">
            <i data-lucide="zap" class="w-4 h-4"></i> Simulate Power Spike
          </button>
          <button id="demo-intrusion-btn" class="px-5 py-2.5 rounded-xl text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 hover:bg-amber-500/30 transition-colors flex items-center gap-2">
            <i data-lucide="eye" class="w-4 h-4"></i> Simulate Night Intrusion
          </button>
          <button id="demo-away-btn" class="px-5 py-2.5 rounded-xl text-xs font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30 hover:bg-purple-500/30 transition-colors flex items-center gap-2">
            <i data-lucide="plane" class="w-4 h-4"></i> Simulate Away Mode
          </button>
        </div>
      </div>

      <!-- Energy Forecast Chart -->
      <div class="glass-card p-6 rounded-2xl">
        <div class="flex items-center justify-between mb-6">
          <div>
            <h3 class="font-bold text-base text-slate-100 flex items-center gap-2">
              <i data-lucide="trending-up" class="w-5 h-5 text-cyan-400"></i>
              Energy Forecast — Next 12 Hours
            </h3>
            <p class="text-xs text-slate-400 mt-0.5 flex items-center gap-1.5">
              <span class="px-2 py-0.5 rounded-full text-[10px] bg-cyan-500/20 text-cyan-400 font-semibold">
                Algorithm: ${modelsReady ? 'XGBoost time-series' : 'Heuristic baseline'}
              </span>
              ${!modelsReady ? '<span class="text-slate-500">· Model trains after ~5 min of data</span>' : ''}
            </p>
          </div>
        </div>
        <div class="h-52 w-full">
          <canvas id="forecast-chart-canvas"></canvas>
        </div>
      </div>

      <!-- Anomaly Events -->
      <div class="glass-card p-6 rounded-2xl" id="anomaly-panel">
        <h3 class="font-bold text-base text-slate-100 mb-5 flex items-center gap-2">
          <i data-lucide="shield-alert" class="w-5 h-5 text-rose-400"></i>
          Recent Anomaly Events
          <span class="ml-auto px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-400">
            Algorithm: IsolationForest + Z-Score
          </span>
        </h3>
        ${anomalyList.length
          ? anomalyList.map(_buildAnomalyRow).join('')
          : `<p class="text-sm text-slate-400 text-center py-6">No anomalies detected yet. Use a demo trigger above to fire the pipeline.</p>`
        }
      </div>

      <!-- LLM Chat Box (Phase 3 — shown greyed out until model is live) -->
      <div class="glass-card p-6 rounded-2xl">
        <h3 class="font-bold text-base text-slate-100 mb-1 flex items-center gap-2">
          <i data-lucide="message-circle" class="w-5 h-5 text-blue-400"></i>
          Natural Language Control
          ${feats.llm_control?.llm_available
            ? '<span class="ml-auto px-2 py-0.5 rounded-full text-[10px] bg-emerald-500/20 text-emerald-400 font-semibold">LLM Connected</span>'
            : '<span class="ml-auto px-2 py-0.5 rounded-full text-[10px] bg-slate-500/20 text-slate-400 font-semibold">Set OPENAI_API_KEY to enable</span>'
          }
        </h3>
        <p class="text-xs text-slate-400 mb-4">Type a command or question in plain English.</p>
        <div class="flex gap-3">
          <input id="llm-chat-input" type="text"
                 placeholder='e.g. "Turn off all bedroom lights" or "Why was my bill high last week?"'
                 class="glass-input flex-1 px-4 py-2.5 rounded-xl text-xs"
                 ${feats.llm_control?.llm_available ? '' : 'disabled'}>
          <button id="llm-send-btn"
                  class="px-5 py-2.5 rounded-xl text-xs font-bold ${feats.llm_control?.llm_available ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:opacity-95' : 'bg-white/5 text-slate-500 cursor-not-allowed'} transition-all"
                  ${feats.llm_control?.llm_available ? '' : 'disabled'}>
            Send
          </button>
        </div>
        <div id="llm-response" class="mt-4 hidden p-4 rounded-xl bg-black/30 border border-white/5 text-xs text-slate-200 leading-relaxed"></div>
      </div>

    </div>`;
  }

  function _featureCard(icon, label, feat, color) {
    if (!feat) return '';
    const enabled = feat.enabled;
    const status  = feat.status || (feat.llm_available ? 'connected' : 'no_key');
    const algo    = feat.algorithm || feat.model || '';

    const statusLabel = {
      active:            '🟢 Active',
      training:          '🟡 Training',
      heuristic_baseline:'🟡 Baseline',
      accumulating_data: '🟡 Collecting',
      connected:         '🟢 Connected',
      no_key:            '⚪ No API Key',
      unavailable:       '🔴 Unavailable',
    }[status] || status;

    return `
    <div class="glass-card p-5 rounded-2xl flex flex-col gap-3">
      <div class="w-10 h-10 rounded-xl bg-${color}-500/20 text-${color}-400 flex items-center justify-center">
        <i data-lucide="${icon}" class="w-5 h-5"></i>
      </div>
      <div>
        <h4 class="font-bold text-sm text-slate-100">${label}</h4>
        <p class="text-[11px] text-slate-400 mt-0.5 font-mono">${algo}</p>
      </div>
      <div class="mt-auto pt-3 border-t border-white/5 text-[11px] ${enabled ? 'text-slate-300' : 'text-slate-500'}">
        ${enabled ? statusLabel : '⚪ Disabled (feature flag)'}
      </div>
    </div>`;
  }

  function _buildAnomalyRow(a) {
    const scoreColor = a.score >= 0.8 ? 'rose' : 'amber';
    const ts = new Date(a.ts).toLocaleString('en-IN', { hour:'2-digit', minute:'2-digit', day:'numeric', month:'short' });
    return `
    <div class="flex items-start gap-4 py-4 border-b border-white/5 last:border-0">
      <div class="w-10 h-10 rounded-xl bg-${scoreColor}-500/20 text-${scoreColor}-400 flex items-center justify-center flex-shrink-0">
        <i data-lucide="alert-triangle" class="w-5 h-5"></i>
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 flex-wrap mb-1">
          <span class="text-xs font-bold text-slate-200">${a.device_id}</span>
          <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-${scoreColor}-500/20 text-${scoreColor}-400">
            Score: ${(a.score * 100).toFixed(0)}%
          </span>
          <span class="px-2 py-0.5 rounded-full text-[10px] font-mono bg-white/5 text-slate-400">
            ${a.algorithm}
          </span>
          <span class="text-[10px] text-slate-500 ml-auto">${ts}</span>
        </div>
        <p class="text-xs text-slate-300 leading-relaxed">${a.explanation || 'Anomaly detected.'}</p>
        ${a.suggested_action ? `<p class="text-[11px] text-cyan-400 mt-1 font-semibold">→ ${a.suggested_action}</p>` : ''}
      </div>
    </div>`;
  }

  function renderAnomalyPanel(anomalies) {
    const panel = document.getElementById('anomaly-panel');
    if (!panel) return;
    const list = panel.querySelector('.anomaly-list') || panel;
    // Only update if panel is visible
    const view = document.getElementById('view-ai');
    if (!view?.classList.contains('active')) return;

    const rows = anomalies.slice(0, 5).map(_buildAnomalyRow).join('');
    const existing = panel.querySelectorAll('.anomaly-row');
    if (!existing.length) return;
    // Prepend new row
    existing[0].insertAdjacentHTML('beforebegin', rows);
    if (window.lucide) lucide.createIcons({ nodes: [panel] });
  }

  function _renderForecastChart(forecast) {
    const canvas = document.getElementById('forecast-chart-canvas');
    if (!canvas || !forecast.length) return;

    const labels = forecast.map(p => p.hour);
    const values = forecast.map(p => p.predicted_kw);
    const isModel = forecast[0]?.source === 'model';

    const ctx = canvas.getContext('2d');
    const grad = ctx.createLinearGradient(0, 0, 0, 200);
    grad.addColorStop(0, 'rgba(139,92,246,0.4)');
    grad.addColorStop(1, 'rgba(59,130,246,0.0)');

    new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: isModel ? 'XGBoost Forecast (kW)' : 'Baseline Estimate (kW)',
          data: values,
          borderColor: '#8b5cf6',
          borderWidth: 2,
          backgroundColor: grad,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#a78bfa',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: true, position: 'top', align: 'end',
            labels: { color: '#94a3b8', font: { size: 11 }, usePointStyle: true } },
          tooltip: {
            backgroundColor: 'rgba(15,23,42,0.95)',
            titleColor: '#f8fafc', bodyColor: '#a78bfa',
            borderColor: 'rgba(139,92,246,0.3)', borderWidth: 1, padding: 10,
          },
        },
        scales: {
          x: { ticks: { color: '#64748b', font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.05)' } },
          y: { ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 11 }, callback: v => v + ' kW' }, grid: { color: 'rgba(255,255,255,0.05)' } },
        },
      },
    });
  }

  function _attachInsightsListeners(view) {
    // Demo buttons
    view.querySelector('#demo-spike-btn')?.addEventListener('click', async () => {
      showToast('⚡ Injecting power spike into the AI pipeline…', 'warning');
      const res = await apiFetch('/api/simulate/spike', { method: 'POST' });
      if (res) {
        showToast(`🚨 Anomaly detected! Score: ${(res.anomaly_score * 100).toFixed(0)}% — check the Anomaly panel.`, 'error', 7000);
        await fetchAndShowAnomalies();
      }
    });

    view.querySelector('#demo-intrusion-btn')?.addEventListener('click', async () => {
      showToast('🔍 Simulating night intrusion on backyard camera…', 'warning');
      const res = await apiFetch('/api/simulate/intrusion', { method: 'POST' });
      if (res) {
        showToast(`🚨 Intrusion alert! Z-Score: ${(res.anomaly_score * 100).toFixed(0)}%`, 'error', 7000);
        await fetchAndShowAnomalies();
      }
    });

    view.querySelector('#demo-away-btn')?.addEventListener('click', async () => {
      showToast('✈️ Switching to away mode — logging device states…', 'info');
      const res = await apiFetch('/api/simulate/away', { method: 'POST' });
      if (res) showToast(`✅ Away mode recorded for ${res.devices_updated} devices. AI will learn this pattern.`, 'success');
    });

    // LLM chat
    const chatInput = view.querySelector('#llm-chat-input');
    const sendBtn   = view.querySelector('#llm-send-btn');
    const respBox   = view.querySelector('#llm-response');

    sendBtn?.addEventListener('click', async () => {
      const msg = chatInput?.value.trim();
      if (!msg) return;
      if (respBox) { respBox.classList.remove('hidden'); respBox.textContent = '🤖 Thinking…'; }
      const res = await apiFetch('/api/llm/chat', {
        method: 'POST',
        body: JSON.stringify({ message: msg }),
      });
      if (respBox) {
        respBox.textContent = res?.response || 'LLM not yet available. Set OPENAI_API_KEY in .env.';
      }
    });

    chatInput?.addEventListener('keydown', e => { if (e.key === 'Enter') sendBtn?.click(); });
  }

  // ── Update AI status badge in header (if it exists) ───────
  function updateAIStatusBadge(data) {
    const badge = document.getElementById('ai-status-badge');
    if (!badge) return;
    if (!data) {
      badge.className = 'w-2 h-2 rounded-full bg-slate-500';
    } else {
      badge.className = 'w-2 h-2 rounded-full bg-emerald-400 animate-pulse';
    }
  }

  // ── Public API ────────────────────────────────────────────
  window.AIBridge = {
    renderInsights,
    isOnline: () => _aiOnline,
    getStatus: () => _lastStatus,
  };

  // ── Start polling loops ───────────────────────────────────
  pollHealth();
  setInterval(pollHealth,          POLL_INTERVAL_MS);
  setInterval(pushDeviceStates,    PUSH_INTERVAL_MS);
  setInterval(fetchAndShowAnomalies, ALERT_INTERVAL_MS);

  console.log('[AETHER AI Bridge] Initialised — polling http://localhost:8089');
})();
