/**
 * IoT Smart Home - Main Application Controller
 */

class SmartHomeApp {
  constructor() {
    this.currentView = "landing";
    this.energyChart = null;
    this.house3D = null;
    this.selectedRoom = "All";
    this.deviceSearchTerm = "";
    this.deviceFilterType = "All";
    this.init();
  }

  init() {
    document.addEventListener("DOMContentLoaded", () => {
      this.setupRouting();
      this.setupClock();
      this.setupSidebar();
      this.setupDashboardControls();
      this.setupDevicesView();
      this.setupAutomationsView();
      this.setupSettingsView();
      this.setupModalHandlers();
      this.setupCameraCanvas();
      this.setupThemeToggle();

      if (typeof SmartHouse3D !== "undefined") {
        this.house3D = new SmartHouse3D("three-canvas-container");
      }

      if (typeof EnergyCharts !== "undefined") {
        this.energyChart = new EnergyCharts("energy-chart-canvas");
        
        // Connect weekly / daily buttons
        const btnDaily = document.getElementById("chart-btn-daily");
        const btnWeekly = document.getElementById("chart-btn-weekly");
        if (btnDaily && btnWeekly) {
          btnDaily.addEventListener("click", () => {
            btnDaily.className = "px-3 py-1 rounded-lg text-xs font-semibold bg-cyan-500 text-black";
            btnWeekly.className = "px-3 py-1 rounded-lg text-xs font-semibold bg-white/5 text-slate-400 hover:text-white";
            this.energyChart.toggleView("daily");
          });
          btnWeekly.addEventListener("click", () => {
            btnWeekly.className = "px-3 py-1 rounded-lg text-xs font-semibold bg-cyan-500 text-black";
            btnDaily.className = "px-3 py-1 rounded-lg text-xs font-semibold bg-white/5 text-slate-400 hover:text-white";
            this.energyChart.toggleView("weekly");
          });
        }
      }

      this.renderDashboardDevices();
      this.updateHeaderStats();

      // Reactive store listeners
      window.store.subscribe("deviceUpdated", ({ device, emitNotification }) => {
        this.syncDeviceUI(device);
        this.updateHeaderStats();
        if (emitNotification) {
          const stateText = device.state ? "turned ON" : "turned OFF";
          this.showToast(device.name, `${device.name} is now ${stateText}`, "info");
        }
      });

      window.store.subscribe("deviceAdded", (device) => {
        this.renderDashboardDevices();
        this.renderDeviceListPage();
        this.updateHeaderStats();
        this.showToast("Device Added", `${device.name} was successfully paired!`, "success");
      });

      window.store.subscribe("automationAdded", (rule) => {
        this.renderAutomationsList();
        this.showToast("Automation Created", `Rule "${rule.title}" is now active.`, "success");
      });

      if (window.lucide) {
        window.lucide.createIcons();
      }
    });
  }

  setupRouting() {
    const navLinks = document.querySelectorAll("[data-nav-target]");
    navLinks.forEach(link => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        const target = link.getAttribute("data-nav-target");
        this.navigateTo(target);
      });
    });

    const mobileMenuBtn = document.getElementById("mobile-menu-btn");
    const mobileDrawer = document.getElementById("mobile-drawer");
    const mobileDrawerClose = document.getElementById("mobile-drawer-close");

    if (mobileMenuBtn && mobileDrawer) {
      mobileMenuBtn.addEventListener("click", () => {
        mobileDrawer.classList.remove("hidden");
      });
    }

    if (mobileDrawerClose && mobileDrawer) {
      mobileDrawerClose.addEventListener("click", () => {
        mobileDrawer.classList.add("hidden");
      });
    }

    const heroGetStarted = document.getElementById("hero-cta-started");
    const heroLiveDemo = document.getElementById("hero-cta-demo");
    if (heroGetStarted) {
      heroGetStarted.addEventListener("click", () => this.navigateTo("dashboard"));
    }
    if (heroLiveDemo) {
      heroLiveDemo.addEventListener("click", () => this.navigateTo("dashboard"));
    }
  }

  navigateTo(viewId) {
    this.currentView = viewId;

    document.querySelectorAll(".app-view").forEach(view => {
      view.classList.remove("active");
    });

    const targetEl = document.getElementById(`view-${viewId}`);
    if (targetEl) {
      targetEl.classList.add("active");
      window.scrollTo({ top: 0, behavior: "smooth" });
    }

    document.querySelectorAll("[data-nav-target]").forEach(link => {
      const isTarget = link.getAttribute("data-nav-target") === viewId;
      link.classList.toggle("text-cyan-400", isTarget);
      link.classList.toggle("bg-white/5", isTarget);
      link.classList.toggle("border-cyan-500/40", isTarget);
    });

    const mobileDrawer = document.getElementById("mobile-drawer");
    if (mobileDrawer) mobileDrawer.classList.add("hidden");

    if (viewId === "dashboard") {
      this.triggerSkeletonLoading(() => {
        this.renderDashboardDevices();
      });
    } else if (viewId === "devices") {
      this.renderDeviceListPage();
    } else if (viewId === "automation") {
      this.renderAutomationsList();
    }

    if (window.lucide) {
      window.lucide.createIcons();
    }
  }

  setupClock() {
    const clockEl = document.getElementById("realtime-clock");
    const dateEl = document.getElementById("realtime-date");

    const updateTime = () => {
      const now = new Date();
      if (clockEl) {
        clockEl.innerText = now.toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: true
        });
      }
      if (dateEl) {
        dateEl.innerText = now.toLocaleDateString("en-US", {
          weekday: "short",
          month: "short",
          day: "numeric"
        });
      }
    };

    updateTime();
    setInterval(updateTime, 1000);
  }

  setupSidebar() {
    const roomButtons = document.querySelectorAll("[data-room-filter]");
    roomButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        const room = btn.getAttribute("data-room-filter");
        this.selectedRoom = room;

        roomButtons.forEach(b => {
          b.classList.remove("bg-cyan-500/20", "text-cyan-400", "border-cyan-500/40");
          b.classList.add("text-slate-400");
        });

        btn.classList.add("bg-cyan-500/20", "text-cyan-400", "border-cyan-500/40");
        btn.classList.remove("text-slate-400");

        this.triggerSkeletonLoading(() => {
          this.renderDashboardDevices();
        });
      });
    });
  }

  triggerSkeletonLoading(callback) {
    const container = document.getElementById("dashboard-device-grid");
    if (!container) return;

    container.innerHTML = `
      <div class="skeleton h-56 rounded-2xl"></div>
      <div class="skeleton h-56 rounded-2xl"></div>
      <div class="skeleton h-56 rounded-2xl"></div>
      <div class="skeleton h-56 rounded-2xl"></div>
      <div class="skeleton h-56 rounded-2xl"></div>
      <div class="skeleton h-56 rounded-2xl"></div>
    `;

    setTimeout(() => {
      callback();
      if (window.lucide) window.lucide.createIcons();
    }, 280);
  }

  setupDashboardControls() {
    // Light Slider & Toggle
    const lightSlider = document.getElementById("ctrl-light-brightness");
    const lightValText = document.getElementById("ctrl-light-val");
    const lightToggle = document.getElementById("ctrl-light-toggle");

    if (lightSlider && lightValText) {
      lightSlider.addEventListener("input", (e) => {
        const val = e.target.value;
        lightValText.innerText = `${val}%`;
        window.store.updateDevice("dev-1", { brightness: parseInt(val), state: val > 0 }, false);
      });
    }

    if (lightToggle) {
      lightToggle.addEventListener("change", (e) => {
        const checked = e.target.checked;
        window.store.updateDevice("dev-1", { state: checked });
        if (lightSlider) lightSlider.value = checked ? 80 : 0;
        if (lightValText) lightValText.innerText = checked ? "80%" : "0%";
      });
    }

    // Thermostat Controls
    const tempDisplay = document.getElementById("ctrl-temp-display");
    const tempMinus = document.getElementById("ctrl-temp-minus");
    const tempPlus = document.getElementById("ctrl-temp-plus");
    const tempDialCircle = document.getElementById("thermostat-dial-circle");

    const updateThermostatDial = (target) => {
      if (tempDisplay) tempDisplay.innerText = `${target}°C`;
      if (tempDialCircle) {
        const minTemp = 16;
        const maxTemp = 32;
        const percent = (target - minTemp) / (maxTemp - minTemp);
        const offset = 440 - (440 * percent);
        tempDialCircle.style.strokeDashoffset = offset;
      }
    };

    if (tempMinus) {
      tempMinus.addEventListener("click", () => {
        const dev = window.store.getDeviceById("dev-2");
        if (dev && dev.targetTemp > 16) {
          const newTarget = dev.targetTemp - 1;
          window.store.updateDevice("dev-2", { targetTemp: newTarget }, false);
          updateThermostatDial(newTarget);
          this.showToast("Thermostat", `Target set to ${newTarget}°C`, "info");
        }
      });
    }

    if (tempPlus) {
      tempPlus.addEventListener("click", () => {
        const dev = window.store.getDeviceById("dev-2");
        if (dev && dev.targetTemp < 32) {
          const newTarget = dev.targetTemp + 1;
          window.store.updateDevice("dev-2", { targetTemp: newTarget }, false);
          updateThermostatDial(newTarget);
          this.showToast("Thermostat", `Target set to ${newTarget}°C`, "info");
        }
      });
    }

    document.querySelectorAll("[data-thermo-mode]").forEach(btn => {
      btn.addEventListener("click", () => {
        const mode = btn.getAttribute("data-thermo-mode");
        document.querySelectorAll("[data-thermo-mode]").forEach(b => {
          b.classList.remove("bg-cyan-500", "text-black", "font-bold");
          b.classList.add("bg-white/5", "text-slate-400");
        });
        btn.classList.add("bg-cyan-500", "text-black", "font-bold");
        btn.classList.remove("bg-white/5", "text-slate-400");
        window.store.updateDevice("dev-2", { mode });
        this.showToast("Thermostat Mode", `Switched to ${mode.toUpperCase()} mode`, "info");
      });
    });

    // Lock Button
    const lockBtn = document.getElementById("ctrl-lock-btn");
    const lockStatusBadge = document.getElementById("ctrl-lock-status");
    const lockIconContainer = document.getElementById("ctrl-lock-icon");

    if (lockBtn) {
      lockBtn.addEventListener("click", () => {
        const dev = window.store.getDeviceById("dev-3");
        const nextState = !dev.locked;
        window.store.updateDevice("dev-3", { locked: nextState });

        if (nextState) {
          lockStatusBadge.innerText = "LOCKED";
          lockStatusBadge.className = "px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
          lockBtn.innerText = "Unlock Entrance";
          lockBtn.className = "w-full py-2.5 rounded-xl font-semibold text-sm transition-all bg-rose-500/20 text-rose-300 border border-rose-500/30 hover:bg-rose-500/30";
          if (lockIconContainer) {
            lockIconContainer.innerHTML = `<i data-lucide="lock" class="w-8 h-8 text-emerald-400"></i>`;
          }
          this.showToast("Smart Lock", "Front Entrance door is now LOCKED securely.", "success");
        } else {
          lockStatusBadge.innerText = "UNLOCKED";
          lockStatusBadge.className = "px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/30";
          lockBtn.innerText = "Lock Entrance";
          lockBtn.className = "w-full py-2.5 rounded-xl font-semibold text-sm transition-all bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30";
          if (lockIconContainer) {
            lockIconContainer.innerHTML = `<i data-lucide="unlock" class="w-8 h-8 text-rose-400"></i>`;
          }
          this.showToast("Smart Lock Alert", "Front Entrance door has been UNLOCKED!", "warning");
        }
        if (window.lucide) window.lucide.createIcons();
      });
    }

    // Fan Speed Controls
    const fanCard = document.getElementById("ctrl-fan-card");
    const fanSpeedButtons = document.querySelectorAll("[data-fan-speed]");

    fanSpeedButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        const speed = btn.getAttribute("data-fan-speed");
        fanSpeedButtons.forEach(b => {
          b.classList.remove("bg-cyan-500", "text-black", "font-bold");
          b.classList.add("bg-white/5", "text-slate-400");
        });
        btn.classList.add("bg-cyan-500", "text-black", "font-bold");
        btn.classList.remove("bg-white/5", "text-slate-400");

        if (fanCard) {
          fanCard.classList.remove("fan-speed-off", "fan-speed-low", "fan-speed-medium", "fan-speed-high");
          fanCard.classList.add(`fan-speed-${speed}`);
        }

        const devState = speed !== "off";
        const powerMap = { off: 0, low: 22, medium: 48, high: 75 };
        window.store.updateDevice("dev-4", { speed, state: devState, power: powerMap[speed] });
        this.showToast("Ceiling Fan", `Fan speed set to ${speed.toUpperCase()}`, "info");
      });
    });

    // 3D House Light Toggle from Hero
    const toggle3DHouseLightBtn = document.getElementById("hero-toggle-lights");
    if (toggle3DHouseLightBtn) {
      toggle3DHouseLightBtn.addEventListener("click", () => {
        if (this.house3D) {
          const isOn = this.house3D.toggleLights();
          toggle3DHouseLightBtn.innerText = isOn ? "Turn Off 3D Lights" : "Turn On 3D Lights";
          this.showToast("3D Villa", isOn ? "Architectural lighting active" : "Night mode active", "info");
        }
      });
    }

    const reset3DViewBtn = document.getElementById("hero-reset-view");
    if (reset3DViewBtn) {
      reset3DViewBtn.addEventListener("click", () => {
        if (this.house3D) {
          this.house3D.resetView();
          this.showToast("3D Camera", "Camera reset to default isometric angle", "info");
        }
      });
    }
  }

  setupCameraCanvas() {
    const canvas = document.getElementById("cam-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    const drawNoise = () => {
      const w = canvas.width;
      const h = canvas.height;
      const imgData = ctx.createImageData(w, h);
      const buffer = new Uint32Array(imgData.data.buffer);

      for (let i = 0; i < buffer.length; i++) {
        const val = (Math.random() * 25) | 0;
        buffer[i] = (255 << 24) | (val << 16) | (val + 10 << 8) | (val + 18);
      }
      ctx.putImageData(imgData, 0, 0);

      // Patio silhouettes
      ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
      ctx.fillRect(0, h - 35, w, 35);
      ctx.fillStyle = "rgba(30, 41, 59, 0.7)";
      ctx.fillRect(35, 10, 15, h - 35);
      ctx.fillRect(w - 50, 10, 15, h - 35);

      const now = new Date();
      ctx.fillStyle = "#38bdf8";
      ctx.font = "10px 'JetBrains Mono', monospace";
      ctx.fillText(now.toISOString().replace("T", " ").substring(0, 19) + " [CAM-01 YARD]", 12, 20);

      requestAnimationFrame(drawNoise);
    };

    drawNoise();

    const snapshotBtn = document.getElementById("cam-snapshot-btn");
    const flashOverlay = document.getElementById("cam-flash");
    if (snapshotBtn && flashOverlay) {
      snapshotBtn.addEventListener("click", () => {
        flashOverlay.classList.remove("opacity-0");
        flashOverlay.classList.add("opacity-90");
        setTimeout(() => {
          flashOverlay.classList.remove("opacity-90");
          flashOverlay.classList.add("opacity-0");
        }, 120);
        this.showToast("Security Snapshot", "High-res frame saved to security archive.", "success");
      });
    }
  }

  renderDashboardDevices() {
    const container = document.getElementById("dashboard-device-grid");
    if (!container) return;

    const devices = window.store.getDevices(this.selectedRoom);
    container.innerHTML = "";

    devices.forEach(dev => {
      const card = document.createElement("div");
      card.className = `glass-card p-5 rounded-2xl flex flex-col justify-between transition-all ${dev.state ? 'border-cyan-500/30' : 'opacity-85'}`;

      let dynamicControlHtml = "";
      if (dev.type === "light") {
        dynamicControlHtml = `
          <div class="mt-4 pt-3 border-t border-white/5">
            <div class="flex justify-between text-xs text-slate-400 mb-1">
              <span>Brightness</span>
              <span class="font-mono text-cyan-400 font-semibold">${dev.brightness || 80}%</span>
            </div>
            <input type="range" min="0" max="100" value="${dev.state ? (dev.brightness || 80) : 0}" 
                   class="device-slider w-full" data-device-id="${dev.id}">
          </div>
        `;
      } else if (dev.type === "thermostat") {
        dynamicControlHtml = `
          <div class="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
            <span class="text-xs text-slate-400">Target Temp</span>
            <span class="text-sm font-bold text-cyan-400 font-mono">${dev.targetTemp || 22}°C</span>
          </div>
        `;
      } else if (dev.type === "lock") {
        dynamicControlHtml = `
          <div class="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
            <span class="text-xs text-slate-400">Battery</span>
            <span class="text-xs font-mono font-semibold text-emerald-400">${dev.battery || 94}%</span>
          </div>
        `;
      } else if (dev.type === "fan") {
        dynamicControlHtml = `
          <div class="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
            <span class="text-xs text-slate-400">Speed</span>
            <span class="text-xs uppercase font-bold text-cyan-400">${dev.speed || 'Medium'}</span>
          </div>
        `;
      } else {
        dynamicControlHtml = `
          <div class="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
            <span class="text-xs text-slate-400">Power Draw</span>
            <span class="text-xs font-mono text-slate-300">${dev.power || 0} W</span>
          </div>
        `;
      }

      card.innerHTML = `
        <div>
          <div class="flex items-start justify-between">
            <div class="w-12 h-12 rounded-xl flex items-center justify-center ${dev.state ? 'bg-cyan-500/20 text-cyan-400' : 'bg-white/5 text-slate-500'}">
              <i data-lucide="${dev.icon || 'cpu'}" class="w-6 h-6"></i>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" class="sr-only switch-input device-toggle" data-device-id="${dev.id}" ${dev.state ? 'checked' : ''}>
              <div class="switch-track w-11 h-6 bg-slate-700 rounded-full transition-colors flex items-center p-0.5">
                <div class="switch-thumb w-5 h-5 bg-white rounded-full transition-transform"></div>
              </div>
            </label>
          </div>
          
          <div class="mt-4">
            <h4 class="font-bold text-base text-slate-100">${dev.name}</h4>
            <div class="flex items-center gap-2 mt-1">
              <span class="text-xs text-slate-400">${dev.room}</span>
              <span class="w-1.5 h-1.5 rounded-full ${dev.status === 'online' ? 'bg-emerald-400' : 'bg-slate-500'}"></span>
              <span class="text-[11px] text-slate-500">${dev.status === 'online' ? 'Online' : 'Offline'}</span>
            </div>
          </div>
        </div>
        ${dynamicControlHtml}
      `;

      container.appendChild(card);
    });

    container.querySelectorAll(".device-toggle").forEach(toggle => {
      toggle.addEventListener("change", (e) => {
        const id = toggle.getAttribute("data-device-id");
        window.store.updateDevice(id, { state: e.target.checked });
      });
    });

    container.querySelectorAll(".device-slider").forEach(slider => {
      slider.addEventListener("input", (e) => {
        const id = slider.getAttribute("data-device-id");
        const val = parseInt(e.target.value);
        window.store.updateDevice(id, { brightness: val, state: val > 0 }, false);
      });
    });

    if (window.lucide) window.lucide.createIcons();
  }

  setupDevicesView() {
    const searchInput = document.getElementById("device-search-input");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        this.deviceSearchTerm = e.target.value.toLowerCase();
        this.renderDeviceListPage();
      });
    }

    document.querySelectorAll("[data-device-filter-pill]").forEach(pill => {
      pill.addEventListener("click", () => {
        document.querySelectorAll("[data-device-filter-pill]").forEach(p => {
          p.classList.remove("bg-cyan-500/20", "text-cyan-400", "border-cyan-500/40");
          p.classList.add("text-slate-400");
        });
        pill.classList.add("bg-cyan-500/20", "text-cyan-400", "border-cyan-500/40");
        pill.classList.remove("text-slate-400");
        this.deviceFilterType = pill.getAttribute("data-device-filter-pill");
        this.renderDeviceListPage();
      });
    });
  }

  renderDeviceListPage() {
    const container = document.getElementById("devices-page-grid");
    if (!container) return;

    let devices = window.store.getDevices();

    if (this.deviceFilterType !== "All") {
      if (this.deviceFilterType === "Online") {
        devices = devices.filter(d => d.status === "online");
      } else if (this.deviceFilterType === "Offline") {
        devices = devices.filter(d => d.status === "offline");
      } else {
        devices = devices.filter(d => d.room === this.deviceFilterType);
      }
    }

    if (this.deviceSearchTerm) {
      devices = devices.filter(d =>
        d.name.toLowerCase().includes(this.deviceSearchTerm) ||
        d.room.toLowerCase().includes(this.deviceSearchTerm) ||
        d.type.toLowerCase().includes(this.deviceSearchTerm)
      );
    }

    container.innerHTML = "";

    if (devices.length === 0) {
      container.innerHTML = `
        <div class="col-span-full text-center py-16">
          <i data-lucide="search-x" class="w-12 h-12 text-slate-500 mx-auto mb-3"></i>
          <p class="text-slate-400 font-medium">No smart devices found matching your criteria.</p>
        </div>
      `;
      if (window.lucide) window.lucide.createIcons();
      return;
    }

    devices.forEach(dev => {
      const card = document.createElement("div");
      card.className = "glass-card p-5 rounded-2xl flex flex-col justify-between";

      card.innerHTML = `
        <div>
          <div class="flex items-center justify-between mb-4">
            <div class="w-12 h-12 rounded-xl flex items-center justify-center ${dev.state ? 'bg-cyan-500/20 text-cyan-400' : 'bg-white/5 text-slate-400'}">
              <i data-lucide="${dev.icon || 'cpu'}" class="w-6 h-6"></i>
            </div>
            <span class="px-2.5 py-1 rounded-full text-xs font-semibold ${dev.status === 'online' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-700/50 text-slate-400 border border-slate-600/30'}">
              ${dev.status.toUpperCase()}
            </span>
          </div>

          <h3 class="font-bold text-lg text-slate-100 mb-1">${dev.name}</h3>
          <p class="text-xs text-slate-400 mb-3">${dev.room} · ${dev.type.toUpperCase()}</p>

          <div class="bg-black/20 rounded-xl p-3 flex items-center justify-between text-xs text-slate-300 mb-4">
            <span>Last Active: <strong class="text-slate-200">${dev.lastActive}</strong></span>
            <span>Power: <strong class="text-cyan-400 font-mono">${dev.power || 0}W</strong></span>
          </div>
        </div>

        <div class="pt-3 border-t border-white/5 flex items-center justify-between">
          <span class="text-xs font-medium text-slate-400">Power State</span>
          <label class="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" class="sr-only switch-input device-list-toggle" data-device-id="${dev.id}" ${dev.state ? 'checked' : ''}>
            <div class="switch-track w-11 h-6 bg-slate-700 rounded-full transition-colors flex items-center p-0.5">
              <div class="switch-thumb w-5 h-5 bg-white rounded-full transition-transform"></div>
            </div>
          </label>
        </div>
      `;
      container.appendChild(card);
    });

    container.querySelectorAll(".device-list-toggle").forEach(toggle => {
      toggle.addEventListener("change", (e) => {
        const id = toggle.getAttribute("data-device-id");
        window.store.updateDevice(id, { state: e.target.checked });
      });
    });

    if (window.lucide) window.lucide.createIcons();
  }

  setupAutomationsView() {}

  renderAutomationsList() {
    const container = document.getElementById("automations-page-grid");
    if (!container) return;

    const rules = window.store.getAutomations();
    container.innerHTML = "";

    rules.forEach(rule => {
      const card = document.createElement("div");
      card.className = "glass-card p-6 rounded-2xl flex flex-col justify-between";

      card.innerHTML = `
        <div>
          <div class="flex items-center justify-between mb-4">
            <span class="px-3 py-1 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20">
              ${rule.category || 'Rule'}
            </span>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" class="sr-only switch-input auto-toggle" data-auto-id="${rule.id}" ${rule.enabled ? 'checked' : ''}>
              <div class="switch-track w-11 h-6 bg-slate-700 rounded-full transition-colors flex items-center p-0.5">
                <div class="switch-thumb w-5 h-5 bg-white rounded-full transition-transform"></div>
              </div>
            </label>
          </div>

          <h3 class="font-bold text-lg text-slate-100 mb-2">${rule.title}</h3>
          <p class="text-sm text-slate-400 mb-4">${rule.desc}</p>

          <div class="space-y-2 text-xs mb-5">
            <div class="p-2.5 rounded-lg bg-black/30 border border-white/5 flex items-center gap-2 text-slate-300">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-400 uppercase">IF</span>
              <span>${rule.trigger}</span>
            </div>
            <div class="p-2.5 rounded-lg bg-black/30 border border-white/5 flex items-center gap-2 text-slate-300">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-400 uppercase">THEN</span>
              <span>${rule.action}</span>
            </div>
          </div>
        </div>

        <div class="pt-3 border-t border-white/5 flex items-center justify-between">
          <span class="text-xs text-slate-400">${rule.enabled ? 'Status: Active' : 'Status: Paused'}</span>
          <button class="test-rule-btn px-3 py-1.5 rounded-lg text-xs font-semibold bg-white/5 hover:bg-white/10 text-cyan-400 transition-colors" data-auto-id="${rule.id}">
            Run Now
          </button>
        </div>
      `;
      container.appendChild(card);
    });

    container.querySelectorAll(".auto-toggle").forEach(toggle => {
      toggle.addEventListener("change", () => {
        const id = toggle.getAttribute("data-auto-id");
        const auto = window.store.toggleAutomation(id);
        if (auto) {
          this.showToast("Automation", `"${auto.title}" is now ${auto.enabled ? 'ENABLED' : 'PAUSED'}`, "info");
        }
      });
    });

    container.querySelectorAll(".test-rule-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-auto-id");
        const auto = window.store.getAutomations().find(a => a.id === id);
        if (auto) {
          this.showToast("Automation Triggered", `Executed "${auto.title}": ${auto.action}`, "success");
        }
      });
    });

    if (window.lucide) window.lucide.createIcons();
  }

  setupSettingsView() {
    const saveProfileBtn = document.getElementById("save-profile-btn");
    if (saveProfileBtn) {
      saveProfileBtn.addEventListener("click", () => {
        const nameInput = document.getElementById("profile-name-input");
        const emailInput = document.getElementById("profile-email-input");
        if (nameInput && emailInput) {
          window.store.user.name = nameInput.value;
          window.store.user.email = emailInput.value;
          this.showToast("Profile Updated", "Account settings saved successfully.", "success");
          this.updateHeaderStats();
        }
      });
    }

    const resetDataBtn = document.getElementById("reset-demo-btn");
    if (resetDataBtn) {
      resetDataBtn.addEventListener("click", () => {
        this.showToast("Demo Reset", "Restoring factory default demo states...", "info");
        setTimeout(() => location.reload(), 1000);
      });
    }
  }

  setupModalHandlers() {
    const openAddDeviceBtn = document.getElementById("open-add-device-modal");
    const closeAddDeviceBtn = document.getElementById("close-add-device-modal");
    const addDeviceModal = document.getElementById("add-device-modal");
    const addDeviceForm = document.getElementById("add-device-form");

    if (openAddDeviceBtn && addDeviceModal) {
      openAddDeviceBtn.addEventListener("click", () => addDeviceModal.classList.remove("hidden"));
    }
    if (closeAddDeviceBtn && addDeviceModal) {
      closeAddDeviceBtn.addEventListener("click", () => addDeviceModal.classList.add("hidden"));
    }
    if (addDeviceForm && addDeviceModal) {
      addDeviceForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const name = document.getElementById("new-device-name").value;
        const room = document.getElementById("new-device-room").value;
        const type = document.getElementById("new-device-type").value;

        const iconMap = {
          light: "lightbulb",
          thermostat: "thermometer",
          lock: "lock",
          fan: "fan",
          camera: "video",
          appliance: "cpu"
        };

        window.store.addDevice({
          name,
          room,
          type,
          icon: iconMap[type] || "cpu",
          power: 25,
          state: true
        });

        addDeviceModal.classList.add("hidden");
        addDeviceForm.reset();
      });
    }

    const openCreateAutoBtn = document.getElementById("open-create-auto-modal");
    const closeCreateAutoBtn = document.getElementById("close-create-auto-modal");
    const createAutoModal = document.getElementById("create-auto-modal");
    const createAutoForm = document.getElementById("create-auto-form");

    if (openCreateAutoBtn && createAutoModal) {
      openCreateAutoBtn.addEventListener("click", () => createAutoModal.classList.remove("hidden"));
    }
    if (closeCreateAutoBtn && createAutoModal) {
      closeCreateAutoBtn.addEventListener("click", () => createAutoModal.classList.add("hidden"));
    }
    if (createAutoForm && createAutoModal) {
      createAutoForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const title = document.getElementById("rule-title").value;
        const trigger = document.getElementById("rule-trigger").value;
        const action = document.getElementById("rule-action").value;
        const category = document.getElementById("rule-category").value;

        window.store.addAutomation({
          title,
          desc: `${trigger} → ${action}`,
          trigger,
          action,
          category
        });

        createAutoModal.classList.add("hidden");
        createAutoForm.reset();
      });
    }
  }

  setupThemeToggle() {
    const themeBtn = document.getElementById("theme-toggle-btn");
    if (!themeBtn) return;

    themeBtn.addEventListener("click", () => {
      document.body.classList.toggle("light-theme");
      const isLight = document.body.classList.contains("light-theme");
      themeBtn.innerHTML = isLight 
        ? `<i data-lucide="moon" class="w-5 h-5 text-slate-800"></i>` 
        : `<i data-lucide="sun" class="w-5 h-5 text-amber-400"></i>`;
      this.showToast("Theme Changed", isLight ? "Light mode enabled" : "Futuristic dark mode active", "info");
      if (window.lucide) window.lucide.createIcons();
    });
  }

  updateHeaderStats() {
    const summary = window.store.getStateSummary();
    const activeBadge = document.getElementById("header-active-count");
    if (activeBadge) {
      activeBadge.innerText = `${summary.activeCount} / ${summary.totalDevices} Active`;
    }

    const userNameEls = document.querySelectorAll(".user-name-display");
    userNameEls.forEach(el => el.innerText = window.store.user.name);

    const userLocEls = document.querySelectorAll(".user-location-display");
    userLocEls.forEach(el => el.innerText = window.store.user.location);
  }

  syncDeviceUI(device) {
    if (device.id === "dev-1") {
      const slider = document.getElementById("ctrl-light-brightness");
      const toggle = document.getElementById("ctrl-light-toggle");
      const val = document.getElementById("ctrl-light-val");
      if (slider) slider.value = device.brightness || 80;
      if (toggle) toggle.checked = device.state;
      if (val) val.innerText = `${device.brightness || 80}%`;
    }
  }

  showToast(title, message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = "toast-item p-4";

    const iconColors = {
      info: "text-cyan-400",
      success: "text-emerald-400",
      warning: "text-amber-400",
      danger: "text-rose-400"
    };

    const iconNames = {
      info: "info",
      success: "check-circle",
      warning: "alert-triangle",
      danger: "shield-alert"
    };

    toast.innerHTML = `
      <div class="flex items-start gap-3">
        <i data-lucide="${iconNames[type] || 'info'}" class="w-5 h-5 ${iconColors[type] || 'text-cyan-400'} mt-0.5 flex-shrink-0"></i>
        <div class="flex-1">
          <h5 class="text-xs font-bold uppercase tracking-wider text-slate-300">${title}</h5>
          <p class="text-sm text-slate-100 font-medium mt-0.5">${message}</p>
        </div>
        <button class="toast-close text-slate-500 hover:text-slate-300">
          <i data-lucide="x" class="w-4 h-4"></i>
        </button>
      </div>
      <div class="toast-progress mt-3"></div>
    `;

    container.appendChild(toast);
    if (window.lucide) window.lucide.createIcons();

    const closeBtn = toast.querySelector(".toast-close");
    if (closeBtn) {
      closeBtn.addEventListener("click", () => {
        toast.classList.add("removing");
        setTimeout(() => toast.remove(), 300);
      });
    }

    setTimeout(() => {
      if (toast.parentElement) {
        toast.classList.add("removing");
        setTimeout(() => toast.remove(), 300);
      }
    }, 3500);
  }
}

window.app = new SmartHomeApp();
