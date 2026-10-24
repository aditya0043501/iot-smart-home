/**
 * Energy Analytics & Real-Time Charts using Chart.js
 */

class EnergyCharts {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.chart = null;
    this.activeView = "daily";
    this.init();
  }

  init() {
    if (!this.canvas) return;

    const ctx = this.canvas.getContext("2d");

    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, "rgba(6, 182, 212, 0.4)");
    gradient.addColorStop(0.7, "rgba(59, 130, 246, 0.1)");
    gradient.addColorStop(1, "rgba(59, 130, 246, 0.0)");

    const dailyLabels = ["12 AM", "3 AM", "6 AM", "9 AM", "12 PM", "3 PM", "6 PM", "9 PM", "Now"];
    const dailyData = [0.3, 0.2, 0.5, 1.1, 1.8, 1.4, 2.2, 2.8, 1.28];
    const yesterdayData = [0.4, 0.3, 0.4, 0.9, 1.6, 1.7, 2.5, 2.4, 1.1];

    this.chart = new Chart(ctx, {
      type: "line",
      data: {
        labels: dailyLabels,
        datasets: [
          {
            label: "Today (kWh)",
            data: dailyData,
            borderColor: "#06b6d4",
            borderWidth: 3,
            backgroundColor: gradient,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: "#38bdf8",
            pointBorderColor: "#ffffff",
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 7
          },
          {
            label: "Yesterday (kWh)",
            data: yesterdayData,
            borderColor: "rgba(148, 163, 184, 0.35)",
            borderWidth: 2,
            borderDash: [5, 5],
            fill: false,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 5
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: "index",
          intersect: false
        },
        plugins: {
          legend: {
            display: true,
            position: "top",
            align: "end",
            labels: {
              color: "#94a3b8",
              font: { family: "Plus Jakarta Sans", size: 12, weight: "500" },
              boxWidth: 14,
              usePointStyle: true
            }
          },
          tooltip: {
            backgroundColor: "rgba(15, 23, 42, 0.95)",
            titleColor: "#f8fafc",
            bodyColor: "#38bdf8",
            borderColor: "rgba(6, 182, 212, 0.3)",
            borderWidth: 1,
            padding: 12,
            displayColors: false,
            titleFont: { family: "Plus Jakarta Sans", size: 13, weight: "600" },
            bodyFont: { family: "JetBrains Mono", size: 12 }
          }
        },
        scales: {
          x: {
            grid: {
              color: "rgba(255, 255, 255, 0.05)",
              drawBorder: false
            },
            ticks: {
              color: "#64748b",
              font: { family: "Plus Jakarta Sans", size: 11 }
            }
          },
          y: {
            grid: {
              color: "rgba(255, 255, 255, 0.05)",
              drawBorder: false
            },
            ticks: {
              color: "#64748b",
              font: { family: "JetBrains Mono", size: 11 },
              callback: (val) => val + " kW"
            }
          }
        }
      }
    });

    this.startLiveStream();
  }

  toggleView(view) {
    if (!this.chart) return;
    this.activeView = view;

    if (view === "weekly") {
      this.chart.data.labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
      this.chart.data.datasets[0].data = [4.8, 5.2, 4.5, 4.9, 5.4, 6.1, 4.2];
      this.chart.data.datasets[0].label = "This Week (kWh)";
      this.chart.data.datasets[1].data = [5.1, 4.9, 4.8, 5.3, 5.0, 5.8, 4.7];
      this.chart.data.datasets[1].label = "Last Week (kWh)";
    } else {
      this.chart.data.labels = ["12 AM", "3 AM", "6 AM", "9 AM", "12 PM", "3 PM", "6 PM", "9 PM", "Now"];
      this.chart.data.datasets[0].data = [0.3, 0.2, 0.5, 1.1, 1.8, 1.4, 2.2, 2.8, 1.28];
      this.chart.data.datasets[0].label = "Today (kWh)";
      this.chart.data.datasets[1].data = [0.4, 0.3, 0.4, 0.9, 1.6, 1.7, 2.5, 2.4, 1.1];
      this.chart.data.datasets[1].label = "Yesterday (kWh)";
    }
    this.chart.update();
  }

  startLiveStream() {
    setInterval(() => {
      if (this.chart && this.activeView === "daily") {
        const lastIdx = this.chart.data.datasets[0].data.length - 1;
        const jitter = (Math.random() - 0.5) * 0.08;
        let current = this.chart.data.datasets[0].data[lastIdx];
        current = Math.max(0.8, Math.min(2.5, +(current + jitter).toFixed(2)));
        this.chart.data.datasets[0].data[lastIdx] = current;
        this.chart.update("none");

        const livePowerEl = document.getElementById("metric-live-power");
        if (livePowerEl) {
          livePowerEl.innerText = current.toFixed(2) + " kW";
        }
      }
    }, 3500);
  }
}

window.EnergyCharts = EnergyCharts;
