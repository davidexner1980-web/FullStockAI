// FullStock AI vNext Ultimate - Chart Management System
class ChartManager {
    constructor() {
        this.charts = new Map();
        this.defaultOptions = this.getDefaultOptions();
        this.colorSchemes = this.getColorSchemes();
        this.currentTheme = localStorage.getItem('theme') || 'dark';
        
        // Chart.js global configuration
        Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
        Chart.defaults.plugins.legend.display = true;
        Chart.defaults.plugins.tooltip.enabled = true;
        Chart.defaults.maintainAspectRatio = false;
        Chart.defaults.responsive = true;
        
        this.setupGlobalDefaults();
    }
    
    setupGlobalDefaults() {
        const isDark = this.currentTheme === 'dark';
        
        Chart.defaults.color = isDark ? '#e5e7eb' : '#374151';
        Chart.defaults.borderColor = isDark ? '#4b5563' : '#d1d5db';
        Chart.defaults.backgroundColor = isDark ? 'rgba(59, 130, 246, 0.1)' : 'rgba(59, 130, 246, 0.1)';
        
        // Grid lines
        Chart.defaults.scales.linear.grid.color = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
        Chart.defaults.scales.category.grid.color = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
        
        // Tick colors
        Chart.defaults.scales.linear.ticks.color = isDark ? '#9ca3af' : '#6b7280';
        Chart.defaults.scales.category.ticks.color = isDark ? '#9ca3af' : '#6b7280';
    }
    
    getDefaultOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        font: {
                            size: 12,
                            weight: 500
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#4b5563',
                    borderWidth: 1,
                    cornerRadius: 8,
                    displayColors: true,
                    padding: 12,
                    titleFont: {
                        size: 14,
                        weight: 600
                    },
                    bodyFont: {
                        size: 13
                    },
                    callbacks: {
                        title: (context) => {
                            return context[0].label;
                        },
                        label: (context) => {
                            const label = context.dataset.label || '';
                            const value = this.formatValue(context.parsed.y, context.dataset.format);
                            return `${label}: ${value}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: true,
                        color: 'rgba(255, 255, 255, 0.1)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#9ca3af',
                        font: {
                            size: 11
                        }
                    }
                },
                y: {
                    grid: {
                        display: true,
                        color: 'rgba(255, 255, 255, 0.1)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#9ca3af',
                        font: {
                            size: 11
                        },
                        callback: function(value, index, values) {
                            return this.formatValue(value, this.options.format);
                        }.bind(this)
                    }
                }
            },
            animation: {
                duration: 750,
                easing: 'easeInOutQuart'
            }
        };
    }
    
    getColorSchemes() {
        return {
            primary: {
                background: 'rgba(59, 130, 246, 0.1)',
                border: 'rgb(59, 130, 246)',
                point: 'rgb(59, 130, 246)'
            },
            success: {
                background: 'rgba(34, 197, 94, 0.1)',
                border: 'rgb(34, 197, 94)',
                point: 'rgb(34, 197, 94)'
            },
            danger: {
                background: 'rgba(239, 68, 68, 0.1)',
                border: 'rgb(239, 68, 68)',
                point: 'rgb(239, 68, 68)'
            },
            warning: {
                background: 'rgba(245, 158, 11, 0.1)',
                border: 'rgb(245, 158, 11)',
                point: 'rgb(245, 158, 11)'
            },
            info: {
                background: 'rgba(14, 165, 233, 0.1)',
                border: 'rgb(14, 165, 233)',
                point: 'rgb(14, 165, 233)'
            },
            gradient: {
                bullish: ['rgba(34, 197, 94, 0.8)', 'rgba(34, 197, 94, 0.1)'],
                bearish: ['rgba(239, 68, 68, 0.8)', 'rgba(239, 68, 68, 0.1)'],
                neutral: ['rgba(156, 163, 175, 0.8)', 'rgba(156, 163, 175, 0.1)']
            }
        };
    }
    
    createPriceChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.error(`Canvas element ${canvasId} not found`);
            return null;
        }
        
        const ctx = canvas.getContext('2d');
        
        const chartOptions = {
            ...this.defaultOptions,
            ...options,
            scales: {
                ...this.defaultOptions.scales,
                y: {
                    ...this.defaultOptions.scales.y,
                    title: {
                        display: true,
                        text: 'Price ($)',
                        color: '#9ca3af',
                        font: {
                            size: 12,
                            weight: 500
                        }
                    },
                    ticks: {
                        ...this.defaultOptions.scales.y.ticks,
                        callback: function(value) {
                            return this.formatCurrency(value);
                        }.bind(this)
                    }
                }
            }
        };
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: data,
            options: chartOptions
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    createVolumeChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        
        const chartOptions = {
            ...this.defaultOptions,
            ...options,
            scales: {
                ...this.defaultOptions.scales,
                y: {
                    ...this.defaultOptions.scales.y,
                    title: {
                        display: true,
                        text: 'Volume',
                        color: '#9ca3af',
                        font: {
                            size: 12,
                            weight: 500
                        }
                    },
                    ticks: {
                        ...this.defaultOptions.scales.y.ticks,
                        callback: function(value) {
                            return this.formatNumber(value);
                        }.bind(this)
                    }
                }
            }
        };
        
        const chart = new Chart(ctx, {
            type: 'bar',
            data: data,
            options: chartOptions
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    createCandlestickChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        
        // Custom candlestick drawing
        const candlestickOptions = {
            ...this.defaultOptions,
            ...options,
            plugins: {
                ...this.defaultOptions.plugins,
                tooltip: {
                    ...this.defaultOptions.plugins.tooltip,
                    callbacks: {
                        title: (context) => context[0].label,
                        label: (context) => {
                            const data = context.raw;
                            return [
                                `Open: ${this.formatCurrency(data.o)}`,
                                `High: ${this.formatCurrency(data.h)}`,
                                `Low: ${this.formatCurrency(data.l)}`,
                                `Close: ${this.formatCurrency(data.c)}`
                            ];
                        }
                    }
                }
            },
            scales: {
                ...this.defaultOptions.scales,
                y: {
                    ...this.defaultOptions.scales.y,
                    title: {
                        display: true,
                        text: 'Price ($)',
                        color: '#9ca3af'
                    }
                }
            }
        };
        
        const chart = new Chart(ctx, {
            type: 'candlestick',
            data: data,
            options: candlestickOptions
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    createPortfolioChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        
        const chartOptions = {
            ...this.defaultOptions,
            ...options,
            plugins: {
                ...this.defaultOptions.plugins,
                legend: {
                    display: true,
                    position: 'right',
                    labels: {
                        generateLabels: (chart) => {
                            const data = chart.data;
                            return data.labels.map((label, index) => ({
                                text: `${label} (${data.datasets[0].data[index]}%)`,
                                fillStyle: data.datasets[0].backgroundColor[index],
                                strokeStyle: data.datasets[0].borderColor[index],
                                lineWidth: 2,
                                index: index
                            }));
                        }
                    }
                }
            }
        };
        
        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: data,
            options: chartOptions
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    createPredictionChart(canvasId, historicalData, predictionData, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.3)');
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0.05)');
        
        const predictionGradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
        predictionGradient.addColorStop(0, 'rgba(34, 197, 94, 0.3)');
        predictionGradient.addColorStop(1, 'rgba(34, 197, 94, 0.05)');
        
        const data = {
            labels: [...historicalData.labels, ...predictionData.labels],
            datasets: [
                {
                    label: 'Historical Price',
                    data: [...historicalData.data, null],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: gradient,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 6
                },
                {
                    label: 'Prediction',
                    data: [historicalData.data[historicalData.data.length - 1], ...predictionData.data],
                    borderColor: 'rgb(34, 197, 94)',
                    backgroundColor: predictionGradient,
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: true,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 6
                },
                {
                    label: 'Confidence Band Upper',
                    data: [null, ...predictionData.upperBand],
                    borderColor: 'rgba(34, 197, 94, 0.3)',
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    fill: false,
                    pointRadius: 0,
                    tension: 0.1
                },
                {
                    label: 'Confidence Band Lower',
                    data: [null, ...predictionData.lowerBand],
                    borderColor: 'rgba(34, 197, 94, 0.3)',
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    fill: '-1',
                    pointRadius: 0,
                    tension: 0.1
                }
            ]
        };
        
        const chartOptions = {
            ...this.defaultOptions,
            ...options,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                ...this.defaultOptions.plugins,
                annotation: {
                    annotations: {
                        line1: {
                            type: 'line',
                            xMin: historicalData.labels.length - 0.5,
                            xMax: historicalData.labels.length - 0.5,
                            borderColor: 'rgba(156, 163, 175, 0.8)',
                            borderWidth: 2,
                            borderDash: [3, 3],
                            label: {
                                enabled: true,
                                content: 'Prediction Start',
                                position: 'top'
                            }
                        }
                    }
                }
            }
        };
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: data,
            options: chartOptions
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    createIndicatorChart(canvasId, data, indicatorType, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        let chartData = data;
        let chartOptions = { ...this.defaultOptions, ...options };
        
        switch (indicatorType) {
            case 'rsi':
                chartData = this.formatRSIData(data);
                chartOptions.scales.y.min = 0;
                chartOptions.scales.y.max = 100;
                chartOptions.plugins.annotation = this.getRSIAnnotations();
                break;
                
            case 'macd':
                chartData = this.formatMACDData(data);
                chartOptions.plugins.legend.display = true;
                break;
                
            case 'bollinger':
                chartData = this.formatBollingerData(data);
                break;
                
            case 'volume':
                return this.createVolumeChart(canvasId, data, options);
        }
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: chartOptions
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    formatRSIData(data) {
        return {
            labels: data.labels,
            datasets: [{
                label: 'RSI',
                data: data.rsi,
                borderColor: 'rgb(147, 51, 234)',
                backgroundColor: 'rgba(147, 51, 234, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.1,
                pointRadius: 0,
                pointHoverRadius: 4
            }]
        };
    }
    
    formatMACDData(data) {
        return {
            labels: data.labels,
            datasets: [
                {
                    label: 'MACD Line',
                    data: data.macd,
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0
                },
                {
                    label: 'Signal Line',
                    data: data.signal,
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0
                },
                {
                    label: 'Histogram',
                    data: data.histogram,
                    type: 'bar',
                    backgroundColor: data.histogram.map(val => val >= 0 ? 
                        'rgba(34, 197, 94, 0.6)' : 'rgba(239, 68, 68, 0.6)'),
                    borderColor: data.histogram.map(val => val >= 0 ? 
                        'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'),
                    borderWidth: 1
                }
            ]
        };
    }
    
    formatBollingerData(data) {
        return {
            labels: data.labels,
            datasets: [
                {
                    label: 'Price',
                    data: data.price,
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0
                },
                {
                    label: 'Upper Band',
                    data: data.upperBand,
                    borderColor: 'rgba(156, 163, 175, 0.8)',
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    fill: false,
                    pointRadius: 0
                },
                {
                    label: 'Lower Band',
                    data: data.lowerBand,
                    borderColor: 'rgba(156, 163, 175, 0.8)',
                    backgroundColor: 'rgba(156, 163, 175, 0.1)',
                    borderWidth: 1,
                    fill: '-1',
                    pointRadius: 0
                },
                {
                    label: 'Middle Band (SMA)',
                    data: data.middleBand,
                    borderColor: 'rgba(245, 158, 11, 0.8)',
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                }
            ]
        };
    }
    
    getRSIAnnotations() {
        return {
            annotations: {
                overbought: {
                    type: 'line',
                    yMin: 70,
                    yMax: 70,
                    borderColor: 'rgba(239, 68, 68, 0.8)',
                    borderWidth: 2,
                    borderDash: [3, 3],
                    label: {
                        enabled: true,
                        content: 'Overbought (70)',
                        position: 'end'
                    }
                },
                oversold: {
                    type: 'line',
                    yMin: 30,
                    yMax: 30,
                    borderColor: 'rgba(34, 197, 94, 0.8)',
                    borderWidth: 2,
                    borderDash: [3, 3],
                    label: {
                        enabled: true,
                        content: 'Oversold (30)',
                        position: 'end'
                    }
                }
            }
        };
    }
    
    // Utility methods
    updateChart(chartId, newData, animation = true) {
        const chart = this.charts.get(chartId);
        if (!chart) return false;
        
        chart.data = newData;
        chart.update(animation ? 'active' : 'none');
        return true;
    }
    
    destroyChart(chartId) {
        const chart = this.charts.get(chartId);
        if (chart) {
            chart.destroy();
            this.charts.delete(chartId);
            return true;
        }
        return false;
    }
    
    destroyAllCharts() {
        this.charts.forEach((chart) => {
            chart.destroy();
        });
        this.charts.clear();
    }
    
    resizeChart(chartId) {
        const chart = this.charts.get(chartId);
        if (chart) {
            chart.resize();
        }
    }
    
    resizeAllCharts() {
        this.charts.forEach((chart) => {
            chart.resize();
        });
    }
    
    exportChart(chartId, format = 'png') {
        const chart = this.charts.get(chartId);
        if (!chart) return null;
        
        return chart.toBase64Image(format, 1.0);
    }
    
    // Formatting helpers
    formatCurrency(value, currency = 'USD', decimals = 2) {
        try {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: currency,
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            }).format(value);
        } catch (error) {
            return `$${value.toFixed(decimals)}`;
        }
    }
    
    formatNumber(value) {
        if (Math.abs(value) >= 1e9) {
            return `${(value / 1e9).toFixed(1)}B`;
        } else if (Math.abs(value) >= 1e6) {
            return `${(value / 1e6).toFixed(1)}M`;
        } else if (Math.abs(value) >= 1e3) {
            return `${(value / 1e3).toFixed(1)}K`;
        } else {
            return value.toLocaleString();
        }
    }
    
    formatValue(value, format = 'currency') {
        switch (format) {
            case 'currency':
                return this.formatCurrency(value);
            case 'percentage':
                return `${value.toFixed(2)}%`;
            case 'number':
                return this.formatNumber(value);
            default:
                return value.toString();
        }
    }
    
    // Theme management
    updateTheme(theme) {
        this.currentTheme = theme;
        this.setupGlobalDefaults();
        
        // Update all existing charts
        this.charts.forEach((chart) => {
            this.applyThemeToChart(chart);
            chart.update('none');
        });
    }
    
    applyThemeToChart(chart) {
        const isDark = this.currentTheme === 'dark';
        
        if (chart.options.scales) {
            Object.keys(chart.options.scales).forEach(scaleKey => {
                const scale = chart.options.scales[scaleKey];
                if (scale.grid) {
                    scale.grid.color = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
                }
                if (scale.ticks) {
                    scale.ticks.color = isDark ? '#9ca3af' : '#6b7280';
                }
                if (scale.title) {
                    scale.title.color = isDark ? '#9ca3af' : '#6b7280';
                }
            });
        }
        
        if (chart.options.plugins && chart.options.plugins.legend) {
            chart.options.plugins.legend.labels.color = isDark ? '#e5e7eb' : '#374151';
        }
    }
}

// Create global chart manager instance
window.ChartManager = new ChartManager();

// Listen for theme changes
document.addEventListener('themeChanged', (event) => {
    window.ChartManager.updateTheme(event.detail.theme);
});

// Handle window resize
window.addEventListener('resize', () => {
    window.ChartManager.resizeAllCharts();
});

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChartManager;
}
