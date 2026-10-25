/**
 * AETHER Smart Home IoT Dashboard — Main Application Controller
 * ---------------------------------------------------------------
 * Full wiring of all DOM elements to window.store.
 * Refactor justification: original app.js was a 1-line stub
 * (console.log only). No existing logic was deleted — this is a
 * net-new implementation of a missing layer.
 * ---------------------------------------------------------------
 */

// ============================================================
// 1. TOAST NOTIFICATION SYSTEM
// ============================================================

function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const icons = { success: 'check-circle', error: 'alert-circle', warning: 'alert-triangle', info: 'info' };
  const colorClass = { success: 'border-emerald-500/40', error: 'border-rose-500/40', warning: 'border-amber-500/40', info: 'border-cyan-500/40' };
  const iconColor  = { success: 'text-emerald-400', error: 'text-rose-400', warning: 'text-amber-400', info: 'text-cyan-400' };

  const toast = document.createElement('div');
  toast.className = `toast-item ${colorClass[type] || colorClass.info}`;
  toast.innerHTML = `
    <div class="flex items-start gap-3 p-4">
      <i data-lucide="${icons[type] || 'info'}" class="w-4 h-4 mt-0.5 flex-shrink-0 ${iconColor[type] || 'text-cyan-400'}"></i>
      <p class="text-xs font-medium text-slate-200 leading-relaxed flex-1">${message}</p>
    </div>
    <div class="toast-progress" style="animation-duration:${duration}ms"></div>`;
  container.appendChild(toast);
  if (window.lucide) lucide.createIcons({ nodes: [toast] });

  setTimeout(() => {
    toast.classList.add('removing');
    setTimeout(() => toast.remove(), 350);
  }, duration);
}

// ============================================================
// 2. VIEW NAVIGATION
// ============================================================

function navigateTo(viewId) {
  const target = document.getElementById('view-' + viewId);
  document.querySelectorAll('.app-view').forEach(v => {
    v.classList.remove('active');
    // Hide inactive views inline: Tailwind's `flex` class on the landing view overrides .app-view{display:none}.
    if (v !== target) v.style.display = 'none';
  });
  if (target) {
    // Force display block before animation
    target.style.display = target.id === 'view-landing' ? '' : 'block';
    requestAnimationFrame(() => target.classList.add('active'));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  document.querySelectorAll('[data-nav-target]').forEach(link => {
    const isActive = link.getAttribute('data-nav-target') === viewId;
    link.className = link.className
      .replace(/text-cyan-400|bg-white\/5|border|border-cyan-500\/40|text-slate-400/g, '').trim();
    if (isActive) {
      link.classList.add('text-cyan-400', 'bg-white/5', 'border', 'border-cyan-500/40');
    } else {
      link.classList.add('text-slate-400');
    }
  });

  document.getElementById('mobile-drawer')?.classList.add('hidden');

  // Lazy-render views on navigation
  if (viewId === 'dashboard')  renderDashboardGrid(store.activeRoom);
  if (viewId === 'devices')    renderDevicesGrid();
  if (viewId === 'automation') renderAutomationsGrid();
  if (viewId === 'ai')         renderAIInsightsView();
  if (viewId === 'ai-lab' && window.AILab) window.AILab.onShow();
}

function initNavigation() {
  document.querySelectorAll('[data-nav-target]').forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      navigateTo(link.getAttribute('data-nav-target'));
    });
  });
  document.getElementById('hero-cta-started')?.addEventListener('click', () => navigateTo('dashboard'));
  document.getElementById('hero-cta-demo')?.addEventListener('click', () => navigateTo('dashboard'));
}

// ============================================================
// 3. REAL-TIME CLOCK
// ============================================================

function updateClock() {
  const now = new Date();
  const timeEl = document.getElementById('realtime-clock');
  const dateEl = document.getElementById('realtime-date');
  if (timeEl) timeEl.textContent = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
  if (dateEl) dateEl.textContent = now.toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric' });
}

// ============================================================
// 4. THEME TOGGLE
// ============================================================

function initThemeToggle() {
  const btn = document.getElementById('theme-toggle-btn');
  if (!btn) return;
  let isDark = document.documentElement.classList.contains('dark');

  btn.addEventListener('click', () => {
    isDark = !isDark;
    document.documentElement.classList.toggle('dark', isDark);
    document.documentElement.classList.toggle('light-theme', !isDark);
    store.user.theme = isDark ? 'dark' : 'light';
    btn.innerHTML = isDark
      ? '<i data-lucide="sun" class="w-5 h-5 text-amber-400"></i>'
      : '<i data-lucide="moon" class="w-5 h-5 text-slate-300"></i>';
    if (window.lucide) lucide.createIcons({ nodes: [btn] });
  });
}

// ============================================================
// 5. MOBILE DRAWER
// ============================================================

function initMobileMenu() {
  const btn      = document.getElementById('mobile-menu-btn');
  const drawer   = document.getElementById('mobile-drawer');
  const closeBtn = document.getElementById('mobile-drawer-close');
  btn?.addEventListener('click', () => drawer?.classList.toggle('hidden'));
  closeBtn?.addEventListener('click', () => drawer?.classList.add('hidden'));
}

// ============================================================
// 6. HEADER SYNC
// ============================================================

function syncHeader() {
  const s = store.getStateSummary();
  const el = document.getElementById('header-active-count');
  if (el) el.textContent = `${s.activeCount} / ${s.totalDevices} Active`;

  document.querySelectorAll('.user-name-display').forEach(e => e.textContent = store.user.name);
  document.querySelectorAll('.user-location-display').forEach(e => e.textContent = store.user.location);

  const livePow = document.getElementById('metric-live-power');
  if (livePow) livePow.textContent = s.energy.currentPowerKw.toFixed(2) + ' kW';
}

// ============================================================
// 7. DEVICE CARD BUILDER (used by both dashboard + devices page)
// ============================================================

const DEVICE_ICON  = { light:'lightbulb', thermostat:'thermometer', lock:'lock', fan:'fan', camera:'video', appliance:'cpu', lamp:'lamp-desk' };
const DEVICE_COLOR = { light:'amber', thermostat:'cyan', lock:'emerald', fan:'purple', camera:'rose', appliance:'blue' };

function deviceExtraInfo(d) {
  if (d.type === 'light')      return `${d.brightness ?? '--'}% brightness`;
  if (d.type === 'thermostat') return `${d.targetTemp ?? '--'}°C · ${d.mode ?? 'cool'}`;
  if (d.type === 'lock')       return `Battery ${d.battery ?? '--'}%`;
  if (d.type === 'fan')        return `Speed: ${d.speed ?? '--'}`;
  if (d.type === 'camera')     return d.recording ? 'Recording' : 'Standby';
  return d.statusText || '';
}

function buildDeviceCard(device) {
  const color   = DEVICE_COLOR[device.type] || 'slate';
  const icon    = DEVICE_ICON[device.type]  || 'cpu';
  const online  = device.status === 'online';
  const dotCls  = online ? 'bg-emerald-400' : 'bg-slate-600';
  const powerW  = device.state && online ? `${device.power ?? 0}W` : '0W';

  return `
  <div class="glass-card p-5 rounded-2xl flex flex-col gap-3" data-device-id="${device.id}">
    <div class="flex items-start justify-between">
      <div class="w-11 h-11 rounded-xl bg-${color}-500/20 text-${color}-400 flex items-center justify-center">
        <i data-lucide="${icon}" class="w-5 h-5"></i>
      </div>
      <label class="relative inline-flex items-center cursor-pointer">
        <input type="checkbox" class="sr-only switch-input device-state-toggle"
               data-device-id="${device.id}" ${device.state ? 'checked' : ''} ${!online ? 'disabled' : ''}>
        <div class="switch-track w-11 h-6 bg-slate-700 rounded-full transition-colors flex items-center p-0.5">
          <div class="switch-thumb w-5 h-5 bg-white rounded-full transition-transform"></div>
        </div>
      </label>
    </div>
    <div>
      <h4 class="font-bold text-sm text-slate-100 truncate">${device.name}</h4>
      <p class="text-[11px] text-slate-400 mt-0.5">${device.room}</p>
    </div>
    <div class="flex items-center justify-between pt-3 border-t border-white/5 text-[11px]">
      <div class="flex items-center gap-1.5 text-slate-400">
        <span class="w-1.5 h-1.5 rounded-full ${dotCls}"></span>
        <span>${online ? 'Online' : 'Offline'}</span>
      </div>
      <span class="font-mono text-slate-400">${deviceExtraInfo(device)}</span>
    </div>
    <div class="flex gap-2">
      <span class="flex-1 py-1 rounded-lg text-[11px] text-center font-mono ${device.state && online ? 'text-emerald-400 bg-emerald-500/10' : 'text-slate-500 bg-white/5'}">${powerW}</span>
      <button class="py-1 px-2.5 rounded-lg text-[11px] font-semibold bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 transition-colors device-delete-btn" data-device-id="${device.id}">
        Remove
      </button>
    </div>
  </div>`;
}

function attachDeviceCardListeners(container) {
  container.querySelectorAll('.device-state-toggle').forEach(toggle => {
    toggle.addEventListener('change', e => {
      const id  = e.target.getAttribute('data-device-id');
      const dev = store.updateDevice(id, { state: e.target.checked });
      if (dev) {
        showToast(`${dev.name} turned <strong>${dev.state ? 'ON' : 'OFF'}</strong>`, dev.state ? 'success' : 'info');
        syncHeader();
      }
    });
  });

  container.querySelectorAll('.device-delete-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      const id  = (e.target.closest('[data-device-id]') || e.target).getAttribute('data-device-id');
      const dev = store.getDeviceById(id);
      if (dev) {
        store.deleteDevice(id);
        showToast(`${dev.name} removed from mesh network.`, 'warning');
        renderDashboardGrid(store.activeRoom);
        renderDevicesGrid();
        syncHeader();
      }
    });
  });
}

// ============================================================
// 8. DASHBOARD DEVICE GRID
// ============================================================

function renderDashboardGrid(room = 'All') {
  const grid = document.getElementById('dashboard-device-grid');
  if (!grid) return;
  const devices = store.getDevices(room === 'All' ? null : room);
  if (!devices.length) {
    grid.innerHTML = `<div class="col-span-3 text-center py-12 text-slate-400 text-sm">No devices in "${room}".</div>`;
    return;
  }
  grid.innerHTML = devices.map(buildDeviceCard).join('');
  if (window.lucide) lucide.createIcons({ nodes: [grid] });
  attachDeviceCardListeners(grid);
}

// ============================================================
// 9. DEVICES PAGE GRID
// ============================================================

let _deviceFilter = 'All';
let _deviceQuery  = '';

function renderDevicesGrid() {
  const grid = document.getElementById('devices-page-grid');
  if (!grid) return;
  let devices = store.getDevices();
  if (_deviceFilter === 'Online')       devices = devices.filter(d => d.status === 'online');
  else if (_deviceFilter === 'Offline') devices = devices.filter(d => d.status === 'offline');
  else if (_deviceFilter !== 'All')     devices = devices.filter(d => d.room === _deviceFilter);
  if (_deviceQuery) {
    const q = _deviceQuery.toLowerCase();
    devices = devices.filter(d => d.name.toLowerCase().includes(q) || d.room.toLowerCase().includes(q));
  }
  if (!devices.length) {
    grid.innerHTML = `<div class="col-span-4 text-center py-12 text-slate-400 text-sm">No devices match your filter.</div>`;
    return;
  }
  grid.innerHTML = devices.map(buildDeviceCard).join('');
  if (window.lucide) lucide.createIcons({ nodes: [grid] });
  attachDeviceCardListeners(grid);
}

function initDevicesPage() {
  const searchInput = document.getElementById('device-search-input');
  searchInput?.addEventListener('input', e => {
    _deviceQuery = e.target.value;
    renderDevicesGrid();
  });

  document.querySelectorAll('[data-device-filter-pill]').forEach(pill => {
    pill.addEventListener('click', () => {
      _deviceFilter = pill.getAttribute('data-device-filter-pill');
      document.querySelectorAll('[data-device-filter-pill]').forEach(p => {
        const active = p.getAttribute('data-device-filter-pill') === _deviceFilter;
        p.className = active
          ? 'px-3 py-1.5 rounded-lg text-xs font-semibold bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
          : 'px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white bg-white/5';
      });
      renderDevicesGrid();
    });
  });
}

// ============================================================
// 10. AUTOMATION GRID
// ============================================================

const AUTO_COLOR = { 'Energy Saving':'cyan', 'Comfort':'purple', 'Security':'emerald', 'Climate':'amber', 'AI Generated':'blue' };

function buildAutomationCard(auto) {
  const color = AUTO_COLOR[auto.category] || 'slate';
  return `
  <div class="glass-card p-6 rounded-2xl flex flex-col gap-4" data-auto-id="${auto.id}">
    <div class="flex items-start justify-between gap-4">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1.5">
          <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-${color}-500/20 text-${color}-400 uppercase tracking-wider">${auto.category}</span>
          ${auto.aiGenerated ? '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-500/20 text-purple-400">✨ AI</span>' : ''}
        </div>
        <h4 class="font-bold text-sm text-slate-100">${auto.title}</h4>
        <p class="text-xs text-slate-400 mt-1 leading-relaxed">${auto.desc}</p>
      </div>
      <label class="relative inline-flex items-center cursor-pointer flex-shrink-0">
        <input type="checkbox" class="sr-only switch-input auto-toggle" data-auto-id="${auto.id}" ${auto.enabled ? 'checked' : ''}>
        <div class="switch-track w-11 h-6 bg-slate-700 rounded-full transition-colors flex items-center p-0.5">
          <div class="switch-thumb w-5 h-5 bg-white rounded-full transition-transform"></div>
        </div>
      </label>
    </div>
    <div class="grid grid-cols-2 gap-3 pt-3 border-t border-white/5 text-[11px]">
      <div class="bg-black/30 p-2.5 rounded-xl">
        <span class="text-cyan-400 font-bold block mb-1 uppercase tracking-wider text-[10px]">IF</span>
        <span class="text-slate-300 leading-relaxed">${auto.trigger}</span>
      </div>
      <div class="bg-black/30 p-2.5 rounded-xl">
        <span class="text-purple-400 font-bold block mb-1 uppercase tracking-wider text-[10px]">THEN</span>
        <span class="text-slate-300 leading-relaxed">${auto.action}</span>
      </div>
    </div>
  </div>`;
}

function renderAutomationsGrid() {
  const grid = document.getElementById('automations-page-grid');
  if (!grid) return;
  const autos = store.getAutomations();
  grid.innerHTML = autos.map(buildAutomationCard).join('');
  grid.querySelectorAll('.auto-toggle').forEach(toggle => {
    toggle.addEventListener('change', e => {
      const id   = e.target.getAttribute('data-auto-id');
      const auto = store.toggleAutomation(id);
      if (auto) showToast(`"${auto.title}" ${auto.enabled ? 'enabled' : 'disabled'}.`, auto.enabled ? 'success' : 'info');
    });
  });
}

// ============================================================
// 11. DASHBOARD WIDGET CONTROLS
// ============================================================

function initDashboardControls() {
  /* ---- Lighting ---- */
  const lightToggle     = document.getElementById('ctrl-light-toggle');
  const lightBrightness = document.getElementById('ctrl-light-brightness');
  const lightVal        = document.getElementById('ctrl-light-val');

  lightToggle?.addEventListener('change', e => {
    store.updateDevice('dev-1', { state: e.target.checked });
    showToast(`Living Room Lights ${e.target.checked ? 'ON' : 'OFF'}`, e.target.checked ? 'success' : 'info');
    syncHeader();
  });
  lightBrightness?.addEventListener('input', e => {
    const v = parseInt(e.target.value);
    if (lightVal) lightVal.textContent = v + '%';
    store.updateDevice('dev-1', { brightness: v }, false);
  });

  /* ---- Thermostat ---- */
  let thermoTemp = 22;
  const tempDisplay  = document.getElementById('ctrl-temp-display');
  const dialCircle   = document.getElementById('thermostat-dial-circle');

  function setThermoTemp(t) {
    thermoTemp = t;
    if (tempDisplay) tempDisplay.textContent = t + '°C';
    if (dialCircle) {
      const pct    = (t - 16) / (30 - 16);
      const offset = 400 - pct * 310;
      dialCircle.style.strokeDashoffset = offset;
      dialCircle.style.stroke = t <= 20 ? '#06b6d4' : t <= 25 ? '#8b5cf6' : '#f59e0b';
    }
    store.updateDevice('dev-2', { targetTemp: t }, false);
  }

  document.getElementById('ctrl-temp-minus')?.addEventListener('click', () => setThermoTemp(Math.max(16, thermoTemp - 1)));
  document.getElementById('ctrl-temp-plus')?.addEventListener('click',  () => setThermoTemp(Math.min(30, thermoTemp + 1)));

  document.querySelectorAll('[data-thermo-mode]').forEach(btn => {
    btn.addEventListener('click', () => {
      const mode = btn.getAttribute('data-thermo-mode');
      store.updateDevice('dev-2', { mode });
      document.querySelectorAll('[data-thermo-mode]').forEach(b => {
        b.className = b.getAttribute('data-thermo-mode') === mode
          ? 'py-1.5 rounded-lg font-bold bg-cyan-500 text-black'
          : 'py-1.5 rounded-lg text-slate-400 hover:text-white';
      });
      showToast(`Climate mode: <strong>${mode.toUpperCase()}</strong>`, 'info');
    });
  });

  /* ---- Smart Lock ---- */
  let isLocked     = true;
  const lockBtn    = document.getElementById('ctrl-lock-btn');
  const lockStatus = document.getElementById('ctrl-lock-status');
  const lockIcon   = document.getElementById('ctrl-lock-icon');

  lockBtn?.addEventListener('click', () => {
    isLocked = !isLocked;
    store.updateDevice('dev-3', { locked: isLocked, state: isLocked });

    if (lockStatus) {
      lockStatus.textContent = isLocked ? 'LOCKED' : 'UNLOCKED';
      lockStatus.className   = isLocked
        ? 'px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
        : 'px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/30';
    }
    if (lockIcon) {
      lockIcon.innerHTML = `<i data-lucide="${isLocked ? 'lock' : 'unlock'}" class="w-6 h-6"></i>`;
      lockIcon.className = isLocked
        ? 'w-12 h-12 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center'
        : 'w-12 h-12 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center';
      if (window.lucide) lucide.createIcons({ nodes: [lockIcon] });
    }
    if (lockBtn) {
      lockBtn.textContent = isLocked ? 'Unlock Entrance' : 'Lock Entrance';
      lockBtn.className   = isLocked
        ? 'w-full py-2.5 rounded-xl font-semibold text-sm transition-all bg-rose-500/20 text-rose-300 border border-rose-500/30 hover:bg-rose-500/30'
        : 'w-full py-2.5 rounded-xl font-semibold text-sm transition-all bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30';
    }
    showToast(isLocked ? '🔒 Front entrance <strong>locked</strong>' : '🔓 Entrance <strong>unlocked</strong> — auto-relock in 30s', isLocked ? 'success' : 'warning');
  });

  /* ---- Ceiling Fan ---- */
  const fanCard = document.getElementById('ctrl-fan-card');
  document.querySelectorAll('[data-fan-speed]').forEach(btn => {
    btn.addEventListener('click', () => {
      const speed = btn.getAttribute('data-fan-speed');
      store.updateDevice('dev-4', { speed, state: speed !== 'off' });
      if (fanCard) fanCard.className = fanCard.className.replace(/fan-speed-\w+/g, '').trim() + ` fan-speed-${speed}`;
      document.querySelectorAll('[data-fan-speed]').forEach(b => {
        b.className = b.getAttribute('data-fan-speed') === speed
          ? 'py-1.5 rounded-lg font-bold bg-cyan-500 text-black'
          : 'py-1.5 rounded-lg text-slate-400 hover:text-white';
      });
      showToast(`Bedroom Fan → <strong>${speed.toUpperCase()}</strong>`, 'info');
      syncHeader();
    });
  });

  /* ---- Camera Snapshot ---- */
  document.getElementById('cam-snapshot-btn')?.addEventListener('click', () => {
    const flash = document.getElementById('cam-flash');
    if (flash) { flash.style.opacity = '0.85'; setTimeout(() => flash.style.opacity = '0', 140); }
    showToast('📸 Snapshot captured — saved to encrypted cloud vault', 'success');
  });
}

// ============================================================
// 12. CAMERA CANVAS — Night-vision noise simulation
// ============================================================

function initCameraCanvas() {
  const canvas = document.getElementById('cam-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function drawFrame() {
    const W = canvas.width, H = canvas.height;
    const id = ctx.createImageData(W, H);
    const d  = id.data;
    for (let i = 0; i < d.length; i += 4) {
      const n = Math.random() * 28 + 8;
      d[i]   = n * 0.15;   // R
      d[i+1] = n * 0.55;   // G  (greenish night-vision)
      d[i+2] = n * 0.12;   // B
      d[i+3] = 255;
    }
    ctx.putImageData(id, 0, 0);
    // Timestamp overlay
    ctx.font = '10px JetBrains Mono, monospace';
    ctx.fillStyle = 'rgba(6,182,212,0.75)';
    const now = new Date();
    ctx.fillText(`CAM-02  ${now.toLocaleTimeString('en-IN')}  BACKYARD`, 10, H - 12);
  }
  setInterval(drawFrame, 85);
}

// ============================================================
// 13. 3D HOUSE CONTROLS
// ============================================================

function init3DHouseControls() {
  const toggleBtn = document.getElementById('hero-toggle-lights');
  const resetBtn  = document.getElementById('hero-reset-view');

  toggleBtn?.addEventListener('click', () => {
    if (!window.smartHouse3D) return;
    const on = window.smartHouse3D.toggleLights();
    toggleBtn.textContent = on ? 'Toggle 3D Lights' : 'Restore Lights';
    showToast(`3D villa interior lights ${on ? 'restored' : 'dimmed'}`, 'info');
  });

  resetBtn?.addEventListener('click', () => window.smartHouse3D?.resetView());
}

// ============================================================
// 14. ROOM FILTER (Dashboard sidebar)
// ============================================================

function initRoomFilter() {
  document.querySelectorAll('[data-room-filter]').forEach(btn => {
    btn.addEventListener('click', () => {
      const room = btn.getAttribute('data-room-filter');
      store.activeRoom = room;
      document.querySelectorAll('[data-room-filter]').forEach(b => {
        const active = b.getAttribute('data-room-filter') === room;
        b.className = active
          ? 'w-full text-left px-3.5 py-2.5 rounded-xl text-xs font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 flex items-center justify-between transition-all'
          : 'w-full text-left px-3.5 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-white/5 flex items-center justify-between transition-all';
      });
      renderDashboardGrid(room);
    });
  });
}

// ============================================================
// 15. ADD DEVICE MODAL
// ============================================================

function initAddDeviceModal() {
  const modal  = document.getElementById('add-device-modal');
  const form   = document.getElementById('add-device-form');
  document.getElementById('open-add-device-modal')?.addEventListener('click', () => modal?.classList.remove('hidden'));
  document.getElementById('close-add-device-modal')?.addEventListener('click', () => modal?.classList.add('hidden'));

  form?.addEventListener('submit', e => {
    e.preventDefault();
    const name = document.getElementById('new-device-name')?.value.trim();
    const room = document.getElementById('new-device-room')?.value;
    const type = document.getElementById('new-device-type')?.value;
    if (!name) return;
    const dev = store.addDevice({ name, room, type, icon: type });
    showToast(`✅ "<strong>${dev.name}</strong>" paired to the mesh network!`, 'success');
    modal?.classList.add('hidden');
    form.reset();
    renderDevicesGrid();
    renderDashboardGrid(store.activeRoom);
    syncHeader();
  });
}

// ============================================================
// 16. CREATE AUTOMATION MODAL
// ============================================================

function initCreateAutoModal() {
  const modal  = document.getElementById('create-auto-modal');
  const form   = document.getElementById('create-auto-form');
  document.getElementById('open-create-auto-modal')?.addEventListener('click', () => modal?.classList.remove('hidden'));
  document.getElementById('close-create-auto-modal')?.addEventListener('click', () => modal?.classList.add('hidden'));

  form?.addEventListener('submit', e => {
    e.preventDefault();
    const title    = document.getElementById('rule-title')?.value.trim();
    const category = document.getElementById('rule-category')?.value;
    const trigger  = document.getElementById('rule-trigger')?.value;
    const action   = document.getElementById('rule-action')?.value;
    if (!title) return;
    store.addAutomation({ title, desc: `When: ${trigger}`, trigger, action, category });
    showToast(`⚡ Automation "<strong>${title}</strong>" created and active!`, 'success');
    modal?.classList.add('hidden');
    form.reset();
    renderAutomationsGrid();
  });
}

// ============================================================
// 17. SETTINGS PAGE
// ============================================================

function initSettingsPage() {
  document.getElementById('save-profile-btn')?.addEventListener('click', () => {
    const name  = document.getElementById('profile-name-input')?.value.trim() || store.user.name;
    const email = document.getElementById('profile-email-input')?.value.trim() || store.user.email;
    store.user.name  = name;
    store.user.email = email;
    document.querySelectorAll('.user-name-display').forEach(el => el.textContent = name);
    showToast('✅ Profile updated successfully.', 'success');
  });

  document.getElementById('reset-demo-btn')?.addEventListener('click', () => {
    showToast('🔄 Resetting demo state…', 'warning', 1500);
    setTimeout(() => location.reload(), 1600);
  });
}

// ============================================================
// 18. ENERGY CHART TIMEFRAME BUTTONS
// ============================================================

function initEnergyChartButtons() {
  const bD = document.getElementById('chart-btn-daily');
  const bW = document.getElementById('chart-btn-weekly');
  bD?.addEventListener('click', () => {
    window.energyCharts?.toggleView('daily');
    bD.className = 'px-3 py-1 rounded-lg text-xs font-semibold bg-cyan-500 text-black';
    if (bW) bW.className = 'px-3 py-1 rounded-lg text-xs font-semibold bg-white/5 text-slate-400 hover:text-white';
  });
  bW?.addEventListener('click', () => {
    window.energyCharts?.toggleView('weekly');
    bW.className = 'px-3 py-1 rounded-lg text-xs font-semibold bg-cyan-500 text-black';
    if (bD) bD.className = 'px-3 py-1 rounded-lg text-xs font-semibold bg-white/5 text-slate-400 hover:text-white';
  });
}

// ============================================================
// 19. STORE SUBSCRIPTIONS
// ============================================================

function initStoreSubscriptions() {
  store.subscribe('deviceUpdated', () => { syncHeader(); });
  store.subscribe('energyUpdated', (energy) => {
    const el = document.getElementById('metric-live-power');
    if (el) el.textContent = energy.currentPowerKw.toFixed(2) + ' kW';
  });
  store.subscribe('stateChanged',  () => syncHeader());
}

// ============================================================
// 20. AI INSIGHTS VIEW — rendered by ai-bridge.js when available
// ============================================================

function renderAIInsightsView() {
  // Delegated to ai-bridge.js which loads after this file.
  // If AI service is not running, show a placeholder.
  if (window.AIBridge) {
    window.AIBridge.renderInsights();
  } else {
    const view = document.getElementById('view-ai');
    if (view && !view.dataset.rendered) {
      view.dataset.rendered = '1';
      // Will be filled by ai-bridge.js on load
    }
  }
}

// ============================================================
// 21. BOOTSTRAP
// ============================================================

function initApp() {
  initNavigation();
  initThemeToggle();
  initMobileMenu();
  initRoomFilter();
  initDashboardControls();
  initCameraCanvas();
  initDevicesPage();
  initAddDeviceModal();
  initCreateAutoModal();
  initSettingsPage();
  initEnergyChartButtons();
  initStoreSubscriptions();

  // Initialize Chart.js energy chart
  window.energyCharts = new EnergyCharts('energy-chart-canvas');

  // Initialize Three.js 3D house
  window.smartHouse3D = new SmartHouse3D('three-canvas-container');
  setTimeout(init3DHouseControls, 600);

  // Initial renders
  renderDashboardGrid('All');
  renderDevicesGrid();
  renderAutomationsGrid();
  syncHeader();

  // Real-time clock
  updateClock();
  setInterval(updateClock, 1000);

  // Lucide icon pass
  if (window.lucide) lucide.createIcons();

  console.log('[AETHER] App initialized. Store:', store.getStateSummary());
}

document.addEventListener('DOMContentLoaded', initApp);