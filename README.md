# AETHER // Smart Home IoT Dashboard & 3D Digital Twin

A futuristic, cyberpunk-inspired IoT smart home dashboard featuring an interactive 3D villa digital twin, real-time energy telemetry analytics, intelligent automation workflows, and multi-device mesh management.

---

## ✨ Features

- **🏛️ 3D Villa Digital Twin (Three.js)**:
  - Procedurally generated 2-story smart architectural model with multi-zone lighting, solar roof panels, EV carport, and landscaping.
  - Interactive orbital mouse/touch controls with damping and LERP camera interpolation.
  - Dynamic daytime/nighttime architectural lighting toggle and kinematic floating particle constellation.
  - Harmonic sine-wave pulsating beacon indicating gateway mesh network status.

- **⚡ Real-Time Energy Telemetry (Chart.js)**:
  - Instantaneous power load tracking vs. historical 24-hour baseline.
  - Daily (24h) and Weekly aggregated consumption views.
  - Live analog electrical fluctuation simulation via stochastic random walk with clamping.
  - Subsystem category breakdown (HVAC, Lighting, Appliances, Standby).

- **🎛️ Unified Device Control Mesh**:
  - Centralized reactive state store using the Publish-Subscribe (Observer) pattern.
  - Dimmable LED lighting controls with real-time slider feedback.
  - Radial thermostat dial with linear SVG dashoffset mapping and multi-mode cooling/heating/eco states.
  - Biometric smart deadbolt lock with automatic status synchronization.
  - Multi-speed ceiling fan control with CSS-driven angular velocity spin simulations.

- **📹 CCTV Security Feed Simulation**:
  - Live high-resolution yard/patio surveillance stream.
  - Direct 32-bit pixel buffer manipulation for authentic 60 FPS infrared camera noise.
  - Interactive snapshot shutter capture with flash overlay and activity archiving.

- **🤖 Intelligent Automation Engine (ECA Pattern)**:
  - Forward-chaining Event-Condition-Action (IF-THEN) rule engine.
  - Geofence, time-based, and ambient sensor triggers.
  - Custom automation builder modal to define and test routines on demand.

- **🌓 Theming & Responsive Design**:
  - Futuristic dark mode with glassmorphic cards and neon cyan/purple accents.
  - One-click toggle to high-contrast modern light theme.
  - Full mobile responsiveness with slide-out navigation drawer.

---

## 🛠️ Tech Stack

- **Frontend Core**: Vanilla JavaScript (ES6+ Classes), HTML5 Canvas, SVG
- **Styling**: Tailwind CSS, Custom Glassmorphism CSS, Keyframe Animation Engine
- **3D Graphics**: [Three.js](https://threejs.org/) (WebGL, PCF Soft Shadows, ACES Filmic Tone Mapping)
- **Charts & Telemetry**: [Chart.js](https://www.chartjs.org/)
- **Icons**: [Lucide Icons](https://lucide.dev/)
- **Backend Server**: Python 3 `http.server.ThreadingHTTPServer` (Dual-stack, CORS-enabled, thread-per-request)

---

## 📁 Project Structure

```text
iot-smart-home/
├── css/
│   └── style.css          # Glassmorphic themes, animations, & neon effects
├── js/
│   ├── app.js             # Main application controller, routing, & DOM binding
│   ├── charts.js          # Energy telemetry analytics & real-time jitter stream
│   ├── store.js           # Central state store (Pub/Sub pattern & mock devices)
│   └── three-house.js     # 3D interactive villa model (Three.js WebGL scene)
├── index.html             # Single-page application markup & modals
├── serve.py               # Multi-threaded local Python development server
├── start_server.bat       # Quick-start script for Windows environments
├── .gitignore             # Git ignore rules
└── README.md              # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites

- A modern web browser supporting WebGL (Chrome, Brave, Edge, Firefox, Safari).
- Python 3.8+ (optional, for local development server).

### Running Locally

1. **Clone the repository**:
   ```bash
   git clone https://github.com/aditya0043501/iot-smart-home.git
   cd iot-smart-home
   ```

2. **Start the local server**:
   - **Using Python**:
     ```bash
     python3 serve.py
     ```
   - **On Windows**: Double-click `start_server.bat`.

3. **Open the Dashboard**:
   Visit [http://localhost:8088](http://localhost:8088) in your web browser.

---

## 📜 License

This project is open source and available under the [MIT License](LICENSE).
