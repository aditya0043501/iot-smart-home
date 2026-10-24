/**
 * IoT Smart Home - Central State Management & Mock Data
 */

class SmartHomeStore {
  constructor() {
    this.listeners = {};
    
    // User Profile
    this.user = {
      name: "Aakash",
      email: "aakash.iot@smarthome.dev",
      location: "Chennai, India",
      role: "Home Administrator",
      avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=250&q=80",
      notifications: {
        push: true,
        email: true,
        securityAlerts: true,
        audioCues: true
      },
      theme: "dark"
    };

    // Rooms
    this.rooms = ["All", "Living Room", "Bedroom", "Kitchen", "Garage"];
    this.activeRoom = "All";

    // 8 Core Devices
    this.devices = [
      {
        id: "dev-1",
        name: "Living Room Main Lights",
        room: "Living Room",
        type: "light",
        state: true,
        brightness: 80,
        colorTemp: "warm",
        power: 28,
        status: "online",
        lastActive: "Just now",
        icon: "lightbulb"
      },
      {
        id: "dev-2",
        name: "Master Climate Thermostat",
        room: "Living Room",
        type: "thermostat",
        state: true,
        currentTemp: 24,
        targetTemp: 22,
        mode: "cool", // cool, heat, eco
        humidity: 52,
        power: 1180,
        status: "online",
        lastActive: "Just now",
        icon: "thermometer"
      },
      {
        id: "dev-3",
        name: "Front Entrance Smart Lock",
        room: "Living Room",
        type: "lock",
        state: true, // locked = true
        locked: true,
        battery: 94,
        lastUnlocked: "Today at 08:30 AM",
        status: "online",
        lastActive: "3m ago",
        icon: "lock"
      },
      {
        id: "dev-4",
        name: "AeroFlow Ceiling Fan",
        room: "Bedroom",
        type: "fan",
        state: true,
        speed: "medium", // off, low, medium, high
        power: 48,
        status: "online",
        lastActive: "Just now",
        icon: "fan"
      },
      {
        id: "dev-5",
        name: "Bedroom Reading Lamp",
        room: "Bedroom",
        type: "light",
        state: false,
        brightness: 45,
        colorTemp: "cyan",
        power: 0,
        status: "online",
        lastActive: "2h ago",
        icon: "lamp"
      },
      {
        id: "dev-6",
        name: "Smart Kitchen Coffee Maker",
        room: "Kitchen",
        type: "appliance",
        state: true,
        statusText: "Ready · Beans 80%",
        power: 18,
        status: "online",
        lastActive: "12m ago",
        icon: "coffee"
      },
      {
        id: "dev-7",
        name: "Backyard Security Cam HD",
        room: "Living Room",
        type: "camera",
        state: true,
        recording: true,
        resolution: "1080p 60fps",
        motionDetected: false,
        status: "online",
        lastActive: "Live Streaming",
        icon: "video"
      },
      {
        id: "dev-8",
        name: "Smart Convection Oven",
        room: "Kitchen",
        type: "appliance",
        state: false,
        statusText: "Standby Mode",
        power: 3,
        status: "offline",
        lastActive: "Yesterday",
        icon: "microwave"
      }
    ];

    // Automations
    this.automations = [
      {
        id: "auto-1",
        title: "Good Night Power Down",
        desc: "Turn off lights at 11:00 PM and lock all doors",
        trigger: "Time: 11:00 PM Every Night",
        action: "All Lights OFF · Doors Locked · Cam Active",
        enabled: true,
        category: "Energy Saving"
      },
      {
        id: "auto-2",
        title: "Morning Routine Comfort",
        desc: "Start coffee brew and set bedroom fan to Low at 06:45 AM",
        trigger: "Time: 06:45 AM Weekdays",
        action: "Coffee Maker ON · Bedroom Fan LOW",
        enabled: true,
        category: "Comfort"
      },
      {
        id: "auto-3",
        title: "Away Mode Perimeter Shield",
        desc: "When all residents leave, lock entrance and activate HD cams",
        trigger: "Geofence: Out of 500m radius",
        action: "Thermostat ECO · Security Guard ARM",
        enabled: true,
        category: "Security"
      },
      {
        id: "auto-4",
        title: "Climate Eco Balancing",
        desc: "If room temperature rises above 26°C, activate AC cooling",
        trigger: "Sensor: Ambient Temp > 26°C",
        action: "Thermostat Set 23°C (Eco Cool)",
        enabled: false,
        category: "Climate"
      }
    ];

    // Energy & Environmental Metrics
    this.energy = {
      usedTodayKwh: 4.2,
      targetKwh: 6.8,
      savedPercentage: 14.5,
      currentPowerKw: 1.28,
      solarGeneratedKwh: 3.1,
      estimatedCost: "₹ 34.50"
    };

    this.homeStatus = {
      overall: "Secure",
      activeAlerts: 0,
      networkMesh: "Matter & Zigbee 3.0",
      gatewayStatus: "Connected (99.9% Uptime)"
    };
  }

  subscribe(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
    return () => {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    };
  }

  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => cb(data));
    }
  }

  getDevices(room = null) {
    if (!room || room === "All") {
      return [...this.devices];
    }
    return this.devices.filter(d => d.room === room);
  }

  getDeviceById(id) {
    return this.devices.find(d => d.id === id);
  }

  updateDevice(id, updates, emitNotification = true) {
    const idx = this.devices.findIndex(d => d.id === id);
    if (idx !== -1) {
      this.devices[idx] = { ...this.devices[idx], ...updates };
      this.recalculateEnergy();
      this.emit("deviceUpdated", { device: this.devices[idx], emitNotification });
      this.emit("stateChanged", this.getStateSummary());
      return this.devices[idx];
    }
    return null;
  }

  addDevice(newDevice) {
    const device = {
      id: "dev-" + (this.devices.length + 1) + "-" + Math.floor(Math.random() * 1000),
      state: true,
      status: "online",
      lastActive: "Just added",
      power: 20,
      brightness: 75,
      ...newDevice
    };
    this.devices.push(device);
    this.emit("deviceAdded", device);
    this.emit("stateChanged", this.getStateSummary());
    return device;
  }

  deleteDevice(id) {
    const idx = this.devices.findIndex(d => d.id === id);
    if (idx !== -1) {
      const removed = this.devices.splice(idx, 1)[0];
      this.emit("deviceRemoved", removed);
      this.emit("stateChanged", this.getStateSummary());
      return removed;
    }
    return null;
  }

  getAutomations() {
    return [...this.automations];
  }

  toggleAutomation(id) {
    const auto = this.automations.find(a => a.id === id);
    if (auto) {
      auto.enabled = !auto.enabled;
      this.emit("automationToggled", auto);
      return auto;
    }
    return null;
  }

  addAutomation(rule) {
    const newRule = {
      id: "auto-" + (this.automations.length + 1),
      enabled: true,
      ...rule
    };
    this.automations.push(newRule);
    this.emit("automationAdded", newRule);
    return newRule;
  }

  recalculateEnergy() {
    let totalWatts = 0;
    this.devices.forEach(d => {
      if (d.state && d.status === "online") {
        totalWatts += (d.power || 15);
      }
    });
    this.energy.currentPowerKw = +(totalWatts / 1000).toFixed(2);
    this.emit("energyUpdated", this.energy);
  }

  getStateSummary() {
    const onlineCount = this.devices.filter(d => d.status === "online").length;
    const activeCount = this.devices.filter(d => d.state && d.status === "online").length;
    return {
      totalDevices: this.devices.length,
      onlineCount,
      activeCount,
      energy: this.energy,
      homeStatus: this.homeStatus
    };
  }
}

window.store = new SmartHomeStore();
