/**
 * FullStock AI Charts - Real Data Visualization
 * Chart.js integration with live price data and prediction overlays
 */

let priceChart = null;
let chartInitialized = false;

/**
 * Initialize Chart
 */
function initializeChart() {
    const ctx = document.getElementById('priceChart');
    if (!ctx) {
        console.error('Chart canvas not found');
        return;
    }
    
    // Chart.js configuration for financial data
    const config = {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Price',
                    data: [],
                    borderColor: 'rgba(102, 126, 234, 1)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 6
                },
                {
                    label: 'Random Forest Prediction',
                    data: [],
                    borderColor: 'rgba(255, 99, 132, 0.8)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0,
                    pointHoverRadius: 6
                },
                {
                    label: 'LSTM Prediction',
                    data: [],
                    borderColor: 'rgba(54, 162, 235, 0.8)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    borderWidth: 2,
                    borderDash: [10, 5],
                    fill: false,
                    pointRadius: 0,
                    pointHoverRadius: 6
                },
                {
                    label: 'XGBoost Prediction',
                    data: [],
                    borderColor: 'rgba(255, 206, 86, 0.8)',
                    backgroundColor: 'rgba(255, 206, 86, 0.1)',
                    borderWidth: 2,
                    borderDash: [15, 5],
                    fill: false,
                    pointRadius: 0,
                    pointHoverRadius: 6
                },
                {
                    label: 'Ensemble Prediction',
                    data: [],
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderWidth: 3,
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 8,
                    pointBackgroundColor: 'rgba(75, 192, 192, 1)'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#ffffff',
                        usePointStyle: true,
                        padding: 20,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(18, 18, 18, 0.9)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    displayColors: true,
                    callbacks: {
                        title: function(context) {
                            return `Date: ${context[0].label}`;
                        },
                        label: function(context) {
                            const value = context.parsed.y;
                            return `${context.dataset.label}: $${value?.toFixed(2) || 'N/A'}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    position: 'bottom',
                    ticks: {
                        color: '#8e9297',
                        maxTicksLimit: 8
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                        drawTicks: false
                    },
                    border: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    beginAtZero: false,
                    ticks: {
                        color: '#8e9297',
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                        drawTicks: false
                    },
                    border: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutCubic'
            }
        }
    };
    
    try {
        priceChart = new Chart(ctx, config);
        chartInitialized = true;
        console.log('Chart initialized successfully');
    } catch (error) {
        console.error('Chart initialization error:', error);
    }
}

/**
 * Update Chart with Real Data
 */
function updateChart(data) {
    if (!priceChart || !chartInitialized) {
        console.warn('Chart not initialized');
        return;
    }
    
    try {
        console.log('Updating chart with data:', data);
        
        // Clear existing data
        priceChart.data.labels = [];
        priceChart.data.datasets.forEach(dataset => {
            dataset.data = [];
        });
        
        // Update historical price data
        if (data.labels && data.prices) {
            priceChart.data.labels = data.labels;
            priceChart.data.datasets[0].data = data.prices.map((price, index) => ({
                x: index,
                y: price
            }));
        }
        
        // Add prediction points if available
        if (data.predictions) {
            const lastIndex = data.labels ? data.labels.length - 1 : 0;
            const nextIndex = lastIndex + 1;
            
            // Random Forest prediction
            if (data.predictions.random_forest && !data.predictions.random_forest.error) {
                priceChart.data.datasets[1].data = [
                    { x: lastIndex, y: data.prices[lastIndex] },
                    { x: nextIndex, y: data.predictions.random_forest.prediction }
                ];
            }
            
            // LSTM prediction
            if (data.predictions.lstm && !data.predictions.lstm.error) {
                priceChart.data.datasets[2].data = [
                    { x: lastIndex, y: data.prices[lastIndex] },
                    { x: nextIndex, y: data.predictions.lstm.prediction }
                ];
            }
            
            // XGBoost prediction
            if (data.predictions.xgboost && !data.predictions.xgboost.error) {
                priceChart.data.datasets[3].data = [
                    { x: lastIndex, y: data.prices[lastIndex] },
                    { x: nextIndex, y: data.predictions.xgboost.prediction }
                ];
            }
            
            // Ensemble prediction (highlighted)
            if (data.predictions.ensemble) {
                priceChart.data.datasets[4].data = [
                    { x: lastIndex, y: data.prices[lastIndex] },
                    { x: nextIndex, y: data.predictions.ensemble.prediction }
                ];
            }
        }
        
        // Update chart
        priceChart.update('none');
        console.log('Chart updated successfully');
        
    } catch (error) {
        console.error('Chart update error:', error);
    }
}

/**
 * Update Chart with Live Price Point
 */
function addLivePricePoint(price, timestamp) {
    if (!priceChart || !chartInitialized) return;
    
    try {
        const labels = priceChart.data.labels;
        const priceData = priceChart.data.datasets[0].data;
        
        // Add new data point
        const newLabel = new Date(timestamp).toLocaleDateString();
        labels.push(newLabel);
        priceData.push({
            x: labels.length - 1,
            y: price
        });
        
        // Keep only last 100 points for performance
        if (labels.length > 100) {
            labels.shift();
            priceData.shift();
            
            // Adjust x coordinates
            priceData.forEach((point, index) => {
                point.x = index;
            });
        }
        
        priceChart.update('none');
        
    } catch (error) {
        console.error('Live price update error:', error);
    }
}

/**
 * Highlight Prediction Line
 */
function highlightPrediction(modelName) {
    if (!priceChart || !chartInitialized) return;
    
    const modelMap = {
        'random_forest': 1,
        'lstm': 2,
        'xgboost': 3,
        'ensemble': 4
    };
    
    const datasetIndex = modelMap[modelName];
    if (datasetIndex !== undefined) {
        // Reset all line widths
        priceChart.data.datasets.forEach((dataset, index) => {
            if (index > 0) {  // Skip price line
                dataset.borderWidth = 2;
            }
        });
        
        // Highlight selected prediction
        priceChart.data.datasets[datasetIndex].borderWidth = 4;
        priceChart.update('none');
    }
}

/**
 * Add Confidence Bands
 */
function addConfidenceBands(predictions) {
    if (!priceChart || !chartInitialized) return;
    
    try {
        // Remove existing confidence bands
        priceChart.data.datasets = priceChart.data.datasets.filter(ds => 
            !ds.label.includes('Confidence')
        );
        
        // Add confidence bands for ensemble prediction
        if (predictions.ensemble && predictions.ensemble.confidence) {
            const confidence = predictions.ensemble.confidence;
            const prediction = predictions.ensemble.prediction;
            const margin = prediction * (1 - confidence) * 0.1; // 10% of uncertainty
            
            const lastIndex = priceChart.data.labels.length - 1;
            const nextIndex = lastIndex + 1;
            
            // Upper confidence band
            priceChart.data.datasets.push({
                label: 'Confidence Upper',
                data: [
                    { x: lastIndex, y: priceChart.data.datasets[0].data[lastIndex]?.y },
                    { x: nextIndex, y: prediction + margin }
                ],
                borderColor: 'rgba(75, 192, 192, 0.3)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                borderWidth: 1,
                fill: false,
                pointRadius: 0,
                tension: 0
            });
            
            // Lower confidence band
            priceChart.data.datasets.push({
                label: 'Confidence Lower',
                data: [
                    { x: lastIndex, y: priceChart.data.datasets[0].data[lastIndex]?.y },
                    { x: nextIndex, y: prediction - margin }
                ],
                borderColor: 'rgba(75, 192, 192, 0.3)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                borderWidth: 1,
                fill: '-1', // Fill to previous dataset
                pointRadius: 0,
                tension: 0
            });
        }
        
        priceChart.update('none');
        
    } catch (error) {
        console.error('Confidence bands error:', error);
    }
}

/**
 * Reset Chart
 */
function resetChart() {
    if (!priceChart || !chartInitialized) return;
    
    priceChart.data.labels = [];
    priceChart.data.datasets.forEach(dataset => {
        dataset.data = [];
    });
    priceChart.update('none');
}

/**
 * Destroy Chart
 */
function destroyChart() {
    if (priceChart) {
        priceChart.destroy();
        priceChart = null;
        chartInitialized = false;
    }
}

/**
 * Export Chart as Image
 */
function exportChartImage() {
    if (!priceChart || !chartInitialized) return null;
    
    try {
        return priceChart.toBase64Image();
    } catch (error) {
        console.error('Chart export error:', error);
        return null;
    }
}

// Mobile-specific chart interactions
function setupMobileChartInteractions() {
    const chartCanvas = document.getElementById('priceChart');
    if (!chartCanvas) return;
    
    let isTouch = false;
    
    chartCanvas.addEventListener('touchstart', () => {
        isTouch = true;
    });
    
    chartCanvas.addEventListener('touchmove', (e) => {
        e.preventDefault(); // Prevent page scrolling while interacting with chart
    });
    
    chartCanvas.addEventListener('mousemove', (e) => {
        if (isTouch) return; // Skip mouse events on touch devices
        
        // Add custom crosshair logic here if needed
    });
}

// Initialize mobile interactions after DOM load
document.addEventListener('DOMContentLoaded', setupMobileChartInteractions);

// Export functions for global access
window.initializeChart = initializeChart;
window.updateChart = updateChart;
window.addLivePricePoint = addLivePricePoint;
window.highlightPrediction = highlightPrediction;
window.addConfidenceBands = addConfidenceBands;
window.resetChart = resetChart;
window.destroyChart = destroyChart;
window.exportChartImage = exportChartImage;