/**
 * Smart Traffic Dashboard App logic
 */

// Determine API Endpoint based on environment
// For local development, we use the local fog node at port 5001.
// When deployed to AWS S3, this placeholder will be replaced by the CI/CD pipeline,
// or use a default AWS API gateway URL.
let API_ENDPOINT = 'http://localhost:5001/status';

if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    // If not local host, use the AWS endpoint (This placeholder will be replaced by GitHub Actions)
    API_ENDPOINT = 'https://woztq8wnt8.execute-api.us-east-1.amazonaws.com/prod/status';
}

// Thresholds mapping (matches Fog Node logic)
const THRESHOLDS = {
    vehicleCount: 30, // High
    speedLow: 20,     // Low
    noiseHigh: 85,    // High
    pollution: 150    // High AQI
};

// DOM Elements
const els = {
    vehicles: document.getElementById('val-vehicles'),
    vTrend: document.getElementById('trend-vehicles'),
    vCard: document.getElementById('card-vehicles'),

    speed: document.getElementById('val-speed'),
    sTrend: document.getElementById('trend-speed'),
    sCard: document.getElementById('card-speed'),

    noise: document.getElementById('val-noise'),
    nTrend: document.getElementById('trend-noise'),
    nCard: document.getElementById('card-noise'),

    pollution: document.getElementById('val-pollution'),
    pTrend: document.getElementById('trend-pollution'),
    pCard: document.getElementById('card-pollution'),

    congestionAlert: document.getElementById('congestion-alert'),
    pollutionAlert: document.getElementById('pollution-alert'),
    lastUpdated: document.getElementById('last-updated-time')
};

// Chart Instances
let trafficChart, envChart;
const MAX_DATA_POINTS = 20; // Number of data points to show before scrolling
const timeLabels = [];

// Initialize Charts
function initCharts() {
    // Traffic Chart (Count & Speed)
    const ctxTraffic = document.getElementById('trafficChart').getContext('2d');
    trafficChart = new Chart(ctxTraffic, {
        type: 'line',
        data: {
            labels: timeLabels,
            datasets: [
                {
                    label: 'Vehicle Count',
                    data: [],
                    borderColor: '#38bdf8', // Light blue
                    backgroundColor: 'rgba(56, 189, 248, 0.1)',
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'y'
                },
                {
                    label: 'Avg Speed (km/h)',
                    data: [],
                    borderColor: '#10b981', // Green
                    backgroundColor: 'transparent',
                    tension: 0.4,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 800, // Smooth transition
                easing: 'linear'
            },
            scales: {
                x: {
                    title: { display: true, text: 'Time', color: '#94a3b8' },
                    ticks: { color: '#94a3b8' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: { display: true, text: 'Vehicles / 15s', color: '#94a3b8' },
                    ticks: { color: '#94a3b8' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: { display: true, text: 'Speed (km/h)', color: '#94a3b8' },
                    ticks: { color: '#94a3b8' },
                    grid: { drawOnChartArea: false } // only draw grid lines for one axis
                }
            },
            plugins: {
                legend: { labels: { color: '#f8fafc' } }
            }
        }
    });

    // Environment Chart (Noise & Pollution)
    const ctxEnv = document.getElementById('envChart').getContext('2d');
    envChart = new Chart(ctxEnv, {
        type: 'line',
        data: {
            labels: timeLabels,
            datasets: [
                {
                    label: 'Noise (dB)',
                    data: [],
                    borderColor: '#f59e0b', // Amber
                    backgroundColor: 'transparent',
                    tension: 0.4,
                    yAxisID: 'y'
                },
                {
                    label: 'Air Pollution (AQI)',
                    data: [],
                    borderColor: '#ef4444', // Red
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 800,
                easing: 'linear'
            },
            scales: {
                x: {
                    title: { display: true, text: 'Time', color: '#94a3b8' },
                    ticks: { color: '#94a3b8' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: { display: true, text: 'Noise (dB)', color: '#94a3b8' },
                    ticks: { color: '#94a3b8' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: { display: true, text: 'AQI', color: '#94a3b8' },
                    ticks: { color: '#94a3b8' },
                    grid: { drawOnChartArea: false }
                }
            },
            plugins: {
                legend: { labels: { color: '#f8fafc' } }
            }
        }
    });
}

// Update UI Function
function updateDashboard(data) {
    if (!data || !data.latest_readings) return;

    const metrics = data.latest_readings;

    // Check Alerts (You can also use 'recent_summaries' alerts from fog node)
    let isCongestion = false;
    let isPollution = false;

    if (data.recent_summaries && data.recent_summaries.length > 0) {
        const latestSummary = data.recent_summaries[0];
        isCongestion = latestSummary.alerts.congestion;
        isPollution = latestSummary.alerts.pollution_warning;
    }

    // Update Vehicle Count
    els.vehicles.textContent = metrics.vehicle_count;
    if (metrics.vehicle_count > THRESHOLDS.vehicleCount) {
        els.vCard.className = 'metric-card glass-panel status-warning';
        els.vTrend.innerHTML = '<span class="text-warning">High Volume</span>';
    } else {
        els.vCard.className = 'metric-card glass-panel status-normal';
        els.vTrend.innerHTML = '<span class="text-success">Normal Volume</span>';
    }

    // Update Speed
    els.speed.textContent = metrics.average_speed;
    if (metrics.average_speed < THRESHOLDS.speedLow) {
        els.sCard.className = 'metric-card glass-panel status-critical';
        els.sTrend.innerHTML = '<span class="text-danger">Slow Traffic</span>';
    } else {
        els.sCard.className = 'metric-card glass-panel status-normal';
        els.sTrend.innerHTML = '<span class="text-success">Flowing</span>';
    }

    // Update Noise
    els.noise.textContent = metrics.noise_level;
    if (metrics.noise_level > THRESHOLDS.noiseHigh) {
        els.nCard.className = 'metric-card glass-panel status-warning';
        els.nTrend.innerHTML = '<span class="text-warning">Loud</span>';
    } else {
        els.nCard.className = 'metric-card glass-panel status-normal';
        els.nTrend.innerHTML = '<span class="text-success">Acceptable</span>';
    }

    // Update Pollution
    els.pollution.textContent = metrics.pollution_level;
    if (metrics.pollution_level > THRESHOLDS.pollution) {
        els.pCard.className = 'metric-card glass-panel status-critical';
        els.pTrend.innerHTML = '<span class="text-danger">Unhealthy</span>';
    } else {
        els.pCard.className = 'metric-card glass-panel status-normal';
        els.pTrend.innerHTML = '<span class="text-success">Good</span>';
    }

    // Toggle Alerts based on flags
    if (isCongestion) {
        els.congestionAlert.classList.remove('hidden');
    } else {
        els.congestionAlert.classList.add('hidden');
    }

    if (isPollution) {
        els.pollutionAlert.classList.remove('hidden');
    } else {
        els.pollutionAlert.classList.add('hidden');
    }

    // Update Timestamp
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    els.lastUpdated.textContent = timeString;

    // Update Charts (Streaming effect)
    updateCharts(timeString, metrics.vehicle_count, metrics.average_speed, metrics.noise_level, metrics.pollution_level);
}

function updateCharts(timeStr, vCount, speed, noise, pollution) {
    // Add current time to labels
    timeLabels.push(timeStr);

    // Push new data points
    trafficChart.data.datasets[0].data.push(vCount);
    trafficChart.data.datasets[1].data.push(speed);

    envChart.data.datasets[0].data.push(noise);
    envChart.data.datasets[1].data.push(pollution);

    // If we exceed MAX_DATA_POINTS, remove oldest data to create moving stream effect
    if (timeLabels.length > MAX_DATA_POINTS) {
        timeLabels.shift();

        trafficChart.data.datasets[0].data.shift();
        trafficChart.data.datasets[1].data.shift();

        envChart.data.datasets[0].data.shift();
        envChart.data.datasets[1].data.shift();
    }

    // Update chart renders
    trafficChart.update();
    envChart.update();
}

// Fetch Logic
async function fetchTrafficData() {
    try {
        const response = await fetch(API_ENDPOINT);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        updateDashboard(data);
    } catch (error) {
        console.error("Could not fetch dashboard data. Retrying...", error);
        // Optional: Show a UI error state here
    }
}

// Initialization and Polling loop
function init() {
    console.log("Starting Smart Traffic Dashboard...");

    // Initialize empty charts
    initCharts();

    // Initial fetch
    fetchTrafficData();

    // The fog node aggregates every 15 seconds. 
    // We poll every 3 seconds for the latest local status to keep the UI snappy and graphs moving.
    setInterval(fetchTrafficData, 3000);
}

// Run when DOM loads
document.addEventListener('DOMContentLoaded', init);
