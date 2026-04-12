// ============= GLOBAL VARIABLES =============

let charts = {};
let chartModes = {
    chartOTD: 'zoom',
    chartDefect: 'zoom',
    chartLeadTime: 'zoom',
    chartCost: 'zoom',
    chartRisk: 'zoom'
};

const chartColors = {
    primary: 'rgba(15, 52, 96, 0.8)',
    secondary: 'rgba(22, 160, 133, 0.8)',
    accent: 'rgba(231, 76, 60, 0.8)',
    warning: 'rgba(243, 156, 18, 0.8)',
    success: 'rgba(39, 174, 96, 0.8)',
    info: 'rgba(52, 152, 219, 0.8)',
    light: 'rgba(149, 165, 181, 0.8)',
    gradient: ['rgba(22, 160, 133, 0.8)', 'rgba(15, 52, 96, 0.8)', 'rgba(231, 76, 60, 0.8)', 'rgba(243, 156, 18, 0.8)']
};

// ============= INITIALIZATION =============

document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    
    // Set default dates
    const today = new Date();
    const sixMonthsAgo = new Date(today.getTime() - 180 * 24 * 60 * 60 * 1000);
    
    document.getElementById('startDate').valueAsDate = sixMonthsAgo;
    document.getElementById('endDate').valueAsDate = today;
    
    // Load suppliers
    loadSuppliers();
    
    // Load initial data
    loadDashboard();
    
    // Event listeners
    document.getElementById('refreshBtn').addEventListener('click', loadDashboard);
    document.getElementById('supplierSelect').addEventListener('change', () => {
        loadDashboard();
        loadMLPredictions();
    });
    document.getElementById('startDate').addEventListener('change', loadDashboard);
    document.getElementById('endDate').addEventListener('change', loadDashboard);
    document.getElementById('statusSelect').addEventListener('change', loadDashboard);
});

// ============= API CALLS =============

async function loadSuppliers() {
    try {
        const response = await fetch('/api/suppliers');
        const suppliers = await response.json();
        
        const select = document.getElementById('supplierSelect');
        suppliers.forEach(s => {
            const option = document.createElement('option');
            option.value = s.supplier_id;
            option.textContent = s.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading suppliers:', error);
    }
}

async function loadDashboard() {
    try {
        // Get filter values
        const supplierId = document.getElementById('supplierSelect').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const status = document.getElementById('statusSelect').value;
        
        // Load summary
        await loadSummary(supplierId, startDate, endDate);
        
        // Load charts
        await loadCharts(supplierId, startDate, endDate, status);
        
        // Load POs
        await loadOpenPOs(supplierId);
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

async function loadSummary(supplierId, startDate, endDate) {
    try {
        let url = `/api/summary?supplier_id=${supplierId}`;
        if (startDate) url += `&start_date=${startDate}`;
        if (endDate) url += `&end_date=${endDate}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        // Update metrics
        updateMetric('metricOTD', data.otd, 'otd');
        updateMetric('metricDefect', data.defect, 'defect');
        updateMetric('metricLT', data.lead_time, 'lt');
        updateMetric('metricRisk', data.risk_score, 'risk');
        
        // Update progress bars
        updateProgressBar('metricOTDBar', Math.min(data.otd, 100));
        updateProgressBar('metricDefectBar', 100 - Math.min(data.defect * 20, 100));
    } catch (error) {
        console.error('Error loading summary:', error);
    }
}

async function loadCharts(supplierId, startDate, endDate, status) {
    try {
        let url = `/api/charts?supplier_id=${supplierId}`;
        if (startDate) url += `&start_date=${startDate}`;
        if (endDate) url += `&end_date=${endDate}`;
        if (status) url += `&status=${status}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        // Render charts
        renderOTDChart(data.otd);
        renderDefectChart(data.defect);
        renderLeadTimeChart(data.lead_time);
        renderCostChart(data.cost);
        renderRiskScoreChart(data.risk_score);
    } catch (error) {
        console.error('Error loading charts:', error);
    }
}

async function loadOpenPOs(supplierId) {
    try {
        let url = `/api/open-pos?supplier_id=${supplierId}`;
        
        const response = await fetch(url);
        const pos = await response.json();
        
        const tbody = document.getElementById('posTableBody');
        tbody.innerHTML = '';
        
        if (pos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No purchase orders found</td></tr>';
            return;
        }
        
        pos.forEach(po => {
            const row = document.createElement('tr');
            const statusClass = po.status === 'Delivered' ? 'status-delivered' : 'status-pending';
            
            row.innerHTML = `
                <td>${po.name}</td>
                <td><strong>PO-${po.po_id}</strong></td>
                <td>${formatDate(po.order_date)}</td>
                <td>${formatDate(po.expected_delivery_date)}</td>
                <td>${po.order_quantity}</td>
                <td><span class="${statusClass}">${po.status}</span></td>
            `;
            
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading POs:', error);
    }
}

async function loadMLPredictions() {
    try {
        const supplierId = document.getElementById('supplierSelect').value;
        
        if (supplierId === 'all') {
            document.getElementById('predictionsContainer').innerHTML = 
                '<div class="prediction-placeholder">Select a specific supplier to view AI predictions</div>';
            return;
        }
        
        const response = await fetch(`/api/ml-predictions/${supplierId}`);
        
        if (!response.ok) {
            document.getElementById('predictionsContainer').innerHTML = 
                '<div class="prediction-placeholder">No predictions available for this supplier</div>';
            return;
        }
        
        const predictions = await response.json();
        
        const container = document.getElementById('predictionsContainer');
        container.innerHTML = `
            <div class="prediction-card" style="border-top: 4px solid #e74c3c;">
                <div class="prediction-label">Delay Risk</div>
                <div class="prediction-value" style="color: ${getRiskColor(predictions.delay_risk)}">${predictions.delay_risk}%</div>
                <div class="prediction-label" style="color: ${getRiskColor(predictions.delay_risk)}">
                    ${getRiskLabel(predictions.delay_risk)}
                </div>
            </div>
            <div class="prediction-card" style="border-top: 4px solid #f39c12;">
                <div class="prediction-label">Quality Risk</div>
                <div class="prediction-value" style="color: ${getRiskColor(predictions.quality_risk)}">${predictions.quality_risk}%</div>
                <div class="prediction-label" style="color: ${getRiskColor(predictions.quality_risk)}">
                    ${getRiskLabel(predictions.quality_risk)}
                </div>
            </div>
            <div class="prediction-card" style="border-top: 4px solid #3498db;">
                <div class="prediction-label">Lead Time</div>
                <div class="prediction-value" style="color: #3498db">${predictions.lead_time}</div>
                <div class="prediction-label">Estimated Category</div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading ML predictions:', error);
    }
}

// ============= CHART RENDERING =============

function renderOTDChart(data) {
    const ctx = document.getElementById('chartOTD').getContext('2d');
    
    if (charts.otd) charts.otd.destroy();
    
    charts.otd = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'OTD %',
                data: data.data,
                backgroundColor: data.data.map(v => v > 80 ? chartColors.success : v > 60 ? chartColors.warning : chartColors.accent),
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                zoom: {
                    zoom: { wheel: { enabled: true, speed: 0.1 }, pinch: { enabled: true }, mode: 'xy' },
                    pan: { enabled: false, mode: 'xy' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { drawBorder: false, color: 'rgba(0,0,0,0.05)' }
                },
                x: { grid: { display: false } }
            }
        }
    });
}

function renderDefectChart(data) {
    const ctx = document.getElementById('chartDefect').getContext('2d');
    
    if (charts.defect) charts.defect.destroy();
    
    charts.defect = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Defect %',
                data: data.data,
                backgroundColor: data.data.map(v => v < 2 ? chartColors.success : v < 4 ? chartColors.warning : chartColors.accent),
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                zoom: {
                    zoom: { wheel: { enabled: true, speed: 0.1 }, pinch: { enabled: true }, mode: 'xy' },
                    pan: { enabled: false, mode: 'xy' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { drawBorder: false, color: 'rgba(0,0,0,0.05)' }
                },
                x: { grid: { display: false } }
            }
        }
    });
}

function renderLeadTimeChart(data) {
    const ctx = document.getElementById('chartLeadTime').getContext('2d');
    
    if (charts.leadTime) charts.leadTime.destroy();
    
    charts.leadTime = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Lead Time (days)',
                data: data.data,
                borderColor: chartColors.secondary,
                backgroundColor: 'rgba(22, 160, 133, 0.1)',
                fill: true,
                tension: 0.4,
                borderWidth: 3,
                pointBackgroundColor: chartColors.secondary,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                zoom: {
                    zoom: { wheel: { enabled: true, speed: 0.1 }, pinch: { enabled: true }, mode: 'xy' },
                    pan: { enabled: false, mode: 'xy' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { drawBorder: false, color: 'rgba(0,0,0,0.05)' }
                },
                x: { grid: { display: false } }
            }
        }
    });
}

function renderCostChart(data) {
    const ctx = document.getElementById('chartCost').getContext('2d');
    
    if (charts.cost) charts.cost.destroy();
    
    charts.cost = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Cost Variance %',
                data: data.data,
                backgroundColor: data.data.map(v => v > 10 ? chartColors.accent : v > 5 ? chartColors.warning : chartColors.success),
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                zoom: {
                    zoom: { wheel: { enabled: true, speed: 0.1 }, pinch: { enabled: true }, mode: 'xy' },
                    pan: { enabled: false, mode: 'xy' }
                }
            },
            scales: {
                y: {
                    grid: { drawBorder: false, color: 'rgba(0,0,0,0.05)' }
                },
                x: { grid: { display: false } }
            }
        }
    });
}

function renderRiskScoreChart(data) {
    const ctx = document.getElementById('chartRisk').getContext('2d');
    
    if (charts.risk) charts.risk.destroy();
    
    const chartType = data.labels.length > 1 ? 'bar' : 'radar';
    
    charts.risk = new Chart(ctx, {
        type: chartType,
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Risk Score',
                data: data.data,
                backgroundColor: data.data.map(v => {
                    if (v < 30) return 'rgba(39, 174, 96, 0.6)';
                    if (v < 60) return 'rgba(243, 156, 18, 0.6)';
                    return 'rgba(231, 76, 60, 0.6)';
                }),
                borderColor: data.data.map(v => {
                    if (v < 30) return '#27ae60';
                    if (v < 60) return '#f39c12';
                    return '#e74c3c';
                }),
                borderWidth: 2,
                borderRadius: chartType === 'bar' ? 8 : 0,
                borderSkipped: false,
                pointBackgroundColor: data.data.map(v => {
                    if (v < 30) return '#27ae60';
                    if (v < 60) return '#f39c12';
                    return '#e74c3c';
                }),
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: chartType === 'radar' ? 6 : 0,
                pointHoverRadius: chartType === 'radar' ? 8 : 0,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                zoom: {
                    zoom: { wheel: { enabled: true, speed: 0.1 }, pinch: { enabled: true }, mode: 'xy' },
                    pan: { enabled: false, mode: 'xy' }
                }
            },
            scales: chartType === 'bar' ? {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { drawBorder: false, color: 'rgba(0,0,0,0.05)' }
                },
                x: { grid: { display: false } }
            } : {}
        }
    });
}

// ============= UTILITY FUNCTIONS =============

function updateMetric(elementId, value, type) {
    const element = document.getElementById(elementId);
    if (type === 'lt') {
        element.textContent = Math.round(value);
    } else {
        element.textContent = value.toFixed(1) + '%';
    }
}

function updateProgressBar(elementId, percentage) {
    const element = document.getElementById(elementId);
    element.style.width = Math.min(percentage, 100) + '%';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(date);
}

function getRiskColor(value) {
    if (value < 30) return '#27ae60'; // Green
    if (value < 60) return '#f39c12'; // Orange
    return '#e74c3c'; // Red
}

function getRiskLabel(value) {
    if (value < 30) return 'Low Risk';
    if (value < 60) return 'Medium Risk';
    return 'High Risk';
}

function resetZoom(chartId) {
    const chartInstance = Object.values(charts).find(c => c && c.canvas && c.canvas.id === chartId);
    if (chartInstance) {
        chartInstance.resetZoom();
    }
}

function toggleMode(chartId, mode) {
    chartModes[chartId] = mode;
    
    // Update button active states
    const buttons = document.querySelectorAll(`[onclick*="${chartId}"]`);
    buttons.forEach(btn => btn.classList.remove('active'));
    
    const modeMap = { 'zoom': 0, 'pan': 1, 'box': 2, 'reset': 3 };
    if (mode !== 'reset' && buttons[modeMap[mode]]) {
        buttons[modeMap[mode]].classList.add('active');
    }
    
    // Update chart plugin options
    const chart = Object.values(charts).find(c => c && c.canvas && c.canvas.id === chartId);
    if (chart) {
        updateChartZoomOptions(chart, mode);
    }
}

function updateChartZoomOptions(chart, mode) {
    if (!chart.options.plugins) chart.options.plugins = {};
    if (!chart.options.plugins.zoom) chart.options.plugins.zoom = {};
    
    if (mode === 'zoom') {
        chart.options.plugins.zoom.zoom = {
            wheel: { enabled: true, speed: 0.1 },
            pinch: { enabled: true },
            mode: 'xy'
        };
        chart.options.plugins.zoom.pan = { enabled: false };
    } else if (mode === 'pan') {
        chart.options.plugins.zoom.zoom = { wheel: { enabled: false }, pinch: { enabled: false } };
        chart.options.plugins.zoom.pan = { enabled: true, mode: 'xy' };
    } else if (mode === 'box') {
        chart.options.plugins.zoom.zoom = {
            wheel: { enabled: false },
            pinch: { enabled: false },
            mode: 'xy'
        };
        chart.options.plugins.zoom.pan = { enabled: false };
    }
    
    chart.update();
}

function resetChart(chartId) {
    const chart = Object.values(charts).find(c => c && c.canvas && c.canvas.id === chartId);
    if (chart && chart.resetZoom) {
        chart.resetZoom();
    }
}

// Auto-refresh every 5 minutes
setInterval(loadDashboard, 5 * 60 * 1000);
