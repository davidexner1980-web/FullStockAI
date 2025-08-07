/**
 * FullStock AI Portfolio Dashboard - Portfolio Analysis & Risk Management
 * Handles portfolio analysis, risk assessment, and optimization recommendations
 */

let currentPortfolio = [];
let allocationChart = null;
let performanceChart = null;
let isAnalyzingPortfolio = false;

/**
 * Initialize Portfolio Dashboard
 */
function initializePortfolioDashboard() {
    console.log('Portfolio Dashboard initialized');
    
    // Setup event listeners
    setupPortfolioEventListeners();
    
    // Initialize WebSocket connection
    if (typeof initializeWebSocket === 'function') {
        initializeWebSocket();
    }
    
    // Setup portfolio charts
    initializePortfolioCharts();
}

/**
 * Setup Portfolio Event Listeners
 */
function setupPortfolioEventListeners() {
    const analyzeBtn = document.getElementById('analyzePortfolioBtn');
    const portfolioInput = document.getElementById('portfolioInput');
    const quickPortfolios = document.querySelectorAll('.quick-portfolio');
    const holdingSortBtns = document.querySelectorAll('.holdings-sort');

    // Analyze portfolio button
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', () => {
            const portfolio = portfolioInput.value.trim();
            if (portfolio) {
                analyzePortfolio(portfolio);
            }
        });
    }

    // Enter key in input
    if (portfolioInput) {
        portfolioInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const portfolio = portfolioInput.value.trim();
                if (portfolio) {
                    analyzePortfolio(portfolio);
                }
            }
        });
    }

    // Quick portfolio buttons
    quickPortfolios.forEach(btn => {
        btn.addEventListener('click', () => {
            const portfolio = btn.getAttribute('data-portfolio');
            portfolioInput.value = portfolio;
            analyzePortfolio(portfolio);
        });
    });

    // Holdings sort buttons
    holdingSortBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            holdingSortBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const sortBy = btn.getAttribute('data-sort');
            sortHoldings(sortBy);
        });
    });
}

/**
 * Analyze Portfolio - Main Function
 */
async function analyzePortfolio(portfolioString) {
    if (isAnalyzingPortfolio) return;
    
    console.log(`Analyzing portfolio: ${portfolioString}`);
    isAnalyzingPortfolio = true;
    
    // Parse portfolio symbols
    currentPortfolio = portfolioString.split(',').map(symbol => symbol.trim().toUpperCase());
    
    // Update UI state
    showPortfolioLoadingState();
    
    try {
        // Fetch portfolio analysis from backend
        const response = await fetch('/api/portfolio/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbols: currentPortfolio
            })
        });
        
        if (!response.ok) {
            throw new Error(`Portfolio API Error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Portfolio analysis successful:', data);
        
        // Update UI with portfolio analysis
        updatePortfolioDisplay(data);
        updatePortfolioUpdates(`📊 Portfolio analysis complete for ${currentPortfolio.length} assets`);
        
        // Show portfolio sections
        showPortfolioResultSections();
        
    } catch (error) {
        console.error('Portfolio analysis error:', error);
        showPortfolioError(`Failed to analyze portfolio: ${error.message}`);
        updatePortfolioUpdates(`❌ Portfolio analysis failed: ${error.message}`);
    } finally {
        hidePortfolioLoadingState();
        isAnalyzingPortfolio = false;
    }
}

/**
 * Update Portfolio Display with Analysis Data
 */
function updatePortfolioDisplay(data) {
    console.log('Updating portfolio display:', data);
    
    // Update portfolio overview
    if (data.overview) {
        updatePortfolioOverview(data.overview);
    }
    
    // Update risk assessment
    if (data.risk_assessment) {
        updateRiskAssessment(data.risk_assessment);
    }
    
    // Update AI recommendations
    if (data.recommendations) {
        updateAIRecommendations(data.recommendations);
    }
    
    // Update holdings analysis
    if (data.holdings) {
        updateHoldingsAnalysis(data.holdings);
    }
    
    // Update charts
    if (data.allocation) {
        updateAllocationChart(data.allocation);
    }
    
    if (data.performance) {
        updatePerformanceChart(data.performance);
    }
}

/**
 * Update Portfolio Overview
 */
function updatePortfolioOverview(overview) {
    console.log('Updating portfolio overview:', overview);
    
    // Total value
    if (overview.total_value !== undefined) {
        document.getElementById('totalValue').textContent = formatCurrency(overview.total_value);
    }
    
    // Total change
    if (overview.total_change !== undefined) {
        const change = overview.total_change;
        const changePercent = overview.total_change_percent || 0;
        
        const totalChangeElement = document.getElementById('totalChange');
        totalChangeElement.textContent = `${change >= 0 ? '+' : ''}$${change.toFixed(2)} (${changePercent.toFixed(2)}%)`;
        totalChangeElement.className = `text-muted ${change >= 0 ? 'text-success' : 'text-danger'}`;
    }
    
    // Daily P&L
    if (overview.daily_pl !== undefined) {
        const dailyPL = overview.daily_pl;
        const dailyPLPercent = overview.daily_pl_percent || 0;
        
        const dailyPLElement = document.getElementById('dailyPL');
        const dailyPLPercentElement = document.getElementById('dailyPLPercent');
        
        dailyPLElement.textContent = `${dailyPL >= 0 ? '+' : ''}$${dailyPL.toFixed(2)}`;
        dailyPLPercentElement.textContent = `${dailyPLPercent >= 0 ? '+' : ''}${dailyPLPercent.toFixed(2)}%`;
        
        const plClass = dailyPL >= 0 ? 'text-success' : 'text-danger';
        dailyPLElement.className = `h4 ${plClass}`;
        dailyPLPercentElement.className = `text-muted ${plClass}`;
    }
    
    // Portfolio Beta
    if (overview.beta !== undefined) {
        document.getElementById('portfolioBeta').textContent = overview.beta.toFixed(2);
    }
    
    // Sharpe Ratio
    if (overview.sharpe_ratio !== undefined) {
        document.getElementById('sharpeRatio').textContent = overview.sharpe_ratio.toFixed(2);
    }
}

/**
 * Update Risk Assessment
 */
function updateRiskAssessment(riskData) {
    console.log('Updating risk assessment:', riskData);
    
    // Overall risk level
    if (riskData.risk_level !== undefined) {
        const riskLevel = riskData.risk_level;
        const riskPercent = (riskLevel * 100).toFixed(0);
        
        const riskElement = document.getElementById('riskLevel');
        const riskBar = document.getElementById('riskProgressBar');
        
        // Determine risk category and color
        let riskCategory, riskClass;
        if (riskLevel < 0.3) {
            riskCategory = 'Low';
            riskClass = 'bg-success';
        } else if (riskLevel < 0.7) {
            riskCategory = 'Medium';
            riskClass = 'bg-warning';
        } else {
            riskCategory = 'High';
            riskClass = 'bg-danger';
        }
        
        riskElement.textContent = `${riskCategory} (${riskPercent}%)`;
        riskElement.className = `badge ${riskClass}`;
        riskBar.style.width = `${riskPercent}%`;
        riskBar.className = `progress-bar ${riskClass}`;
    }
    
    // Diversification score
    if (riskData.diversification_score !== undefined) {
        const diversificationPercent = (riskData.diversification_score * 100).toFixed(0);
        document.getElementById('diversificationScore').textContent = `${diversificationPercent}%`;
        document.getElementById('diversificationBar').style.width = `${diversificationPercent}%`;
    }
    
    // Volatility
    if (riskData.volatility_30d !== undefined) {
        const volatilityPercent = (riskData.volatility_30d * 100).toFixed(1);
        document.getElementById('volatility30D').textContent = `${volatilityPercent}%`;
    }
    
    // Max drawdown
    if (riskData.max_drawdown !== undefined) {
        const maxDrawdownPercent = (riskData.max_drawdown * 100).toFixed(1);
        document.getElementById('maxDrawdown').textContent = `-${maxDrawdownPercent}%`;
    }
}

/**
 * Update AI Recommendations
 */
function updateAIRecommendations(recommendations) {
    const recommendationsContainer = document.getElementById('aiRecommendations');
    if (!recommendationsContainer) return;
    
    if (recommendations && recommendations.length > 0) {
        recommendationsContainer.innerHTML = '';
        
        recommendations.forEach(recommendation => {
            const recElement = document.createElement('div');
            recElement.className = 'mb-3 p-2 rounded glass-effect';
            
            const priority = recommendation.priority || 'medium';
            const icon = priority === 'high' ? '🔴' : priority === 'low' ? '🟢' : '🟡';
            
            recElement.innerHTML = `
                <div class="d-flex align-items-start">
                    <div class="me-2">${icon}</div>
                    <div class="flex-grow-1">
                        <strong>${recommendation.title || 'Recommendation'}</strong><br>
                        <span class="text-muted">${recommendation.description}</span>
                        ${recommendation.impact ? `<br><small class="text-info">Expected impact: ${recommendation.impact}</small>` : ''}
                    </div>
                </div>
            `;
            
            recommendationsContainer.appendChild(recElement);
        });
    } else {
        recommendationsContainer.innerHTML = '<p class="text-muted text-center">No recommendations at this time</p>';
    }
}

/**
 * Update Holdings Analysis
 */
function updateHoldingsAnalysis(holdings) {
    const holdingsTableBody = document.getElementById('holdingsTableBody');
    if (!holdingsTableBody) return;
    
    if (holdings && holdings.length > 0) {
        holdingsTableBody.innerHTML = '';
        
        holdings.forEach(holding => {
            const row = document.createElement('tr');
            
            // Determine change color
            const change = holding.change_1d || 0;
            const changeClass = change >= 0 ? 'text-success' : 'text-danger';
            
            // Risk score color
            const riskScore = holding.risk_score || 0;
            const riskClass = riskScore < 0.3 ? 'text-success' : riskScore > 0.7 ? 'text-danger' : 'text-warning';
            
            row.innerHTML = `
                <td>
                    <strong>${holding.symbol}</strong><br>
                    <small class="text-muted">${holding.name || holding.symbol}</small>
                </td>
                <td>
                    <div class="fw-bold">${(holding.weight * 100).toFixed(1)}%</div>
                    <div class="progress mt-1" style="height: 4px;">
                        <div class="progress-bar" style="width: ${(holding.weight * 100).toFixed(1)}%"></div>
                    </div>
                </td>
                <td>
                    <strong>$${holding.current_price.toFixed(2)}</strong>
                </td>
                <td>
                    <div class="${changeClass}">
                        ${change >= 0 ? '+' : ''}${change.toFixed(2)}%
                    </div>
                </td>
                <td>
                    ${holding.prediction ? 
                        `<div class="text-info">$${holding.prediction.toFixed(2)}</div>` : 
                        '<span class="text-muted">--</span>'
                    }
                </td>
                <td>
                    <span class="${riskClass}">${(riskScore * 100).toFixed(0)}%</span>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary btn-sm analyze-holding" data-symbol="${holding.symbol}">
                            <i data-feather="trending-up" width="12" height="12"></i>
                        </button>
                        <button class="btn btn-outline-secondary btn-sm" data-bs-toggle="tooltip" title="View Details">
                            <i data-feather="info" width="12" height="12"></i>
                        </button>
                    </div>
                </td>
            `;
            
            holdingsTableBody.appendChild(row);
        });
        
        // Add event listeners to analyze buttons
        document.querySelectorAll('.analyze-holding').forEach(btn => {
            btn.addEventListener('click', () => {
                const symbol = btn.getAttribute('data-symbol');
                window.open(`index.html?ticker=${symbol}`, '_blank');
            });
        });
        
        // Re-initialize feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
        
    } else {
        holdingsTableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No holdings data available</td></tr>';
    }
}

/**
 * Initialize Portfolio Charts
 */
function initializePortfolioCharts() {
    // Allocation Chart (Doughnut)
    const allocationCtx = document.getElementById('allocationChart');
    if (allocationCtx) {
        allocationChart = new Chart(allocationCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(255, 99, 132, 0.8)', 
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 206, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(153, 102, 255, 0.8)'
                    ],
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: '#ffffff',
                            padding: 15,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(18, 18, 18, 0.9)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${context.label}: ${percentage}%`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Performance Chart (Line)
    const performanceCtx = document.getElementById('performanceChart');
    if (performanceCtx) {
        performanceChart = new Chart(performanceCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Portfolio',
                        data: [],
                        borderColor: 'rgba(102, 126, 234, 1)',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.1
                    },
                    {
                        label: 'S&P 500',
                        data: [],
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)', 
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#ffffff'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(18, 18, 18, 0.9)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff'
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#8e9297' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y: {
                        ticks: { 
                            color: '#8e9297',
                            callback: function(value) {
                                return value.toFixed(1) + '%';
                            }
                        },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    }
                }
            }
        });
    }
}

/**
 * Update Allocation Chart
 */
function updateAllocationChart(allocationData) {
    if (!allocationChart) return;
    
    try {
        allocationChart.data.labels = allocationData.labels || [];
        allocationChart.data.datasets[0].data = allocationData.values || [];
        allocationChart.update();
    } catch (error) {
        console.error('Allocation chart update error:', error);
    }
}

/**
 * Update Performance Chart
 */
function updatePerformanceChart(performanceData) {
    if (!performanceChart) return;
    
    try {
        performanceChart.data.labels = performanceData.dates || [];
        performanceChart.data.datasets[0].data = performanceData.portfolio_returns || [];
        performanceChart.data.datasets[1].data = performanceData.benchmark_returns || [];
        performanceChart.update();
    } catch (error) {
        console.error('Performance chart update error:', error);
    }
}

/**
 * Sort Holdings Table
 */
function sortHoldings(sortBy) {
    // This would sort the existing table rows by the specified criteria
    console.log(`Sorting holdings by: ${sortBy}`);
    // Implementation would depend on the current data structure
}

/**
 * Show/Hide Portfolio UI Sections
 */
function showPortfolioResultSections() {
    document.getElementById('portfolioOverviewSection').style.display = 'block';
    document.getElementById('riskAssessmentSection').style.display = 'block';
    document.getElementById('portfolioChartsSection').style.display = 'block';
    document.getElementById('holdingsSection').style.display = 'block';
}

function showPortfolioLoadingState() {
    const analyzeBtn = document.getElementById('analyzePortfolioBtn');
    const analyzeText = document.getElementById('analyzePortfolioText');
    const loadingOverlay = document.getElementById('portfolioLoadingOverlay');
    
    if (analyzeBtn) analyzeBtn.disabled = true;
    if (analyzeText) analyzeText.textContent = 'Analyzing...';
    if (loadingOverlay) loadingOverlay.style.display = 'flex';
    
    // Update loading messages
    const loadingMessages = [
        'Calculating risk metrics...',
        'Analyzing correlations...',
        'Computing optimization...',
        'Generating recommendations...'
    ];
    
    let msgIndex = 0;
    const portfolioLoadingInterval = setInterval(() => {
        const loadingTextElement = document.getElementById('portfolioLoadingText');
        if (loadingTextElement) {
            loadingTextElement.textContent = loadingMessages[msgIndex];
            msgIndex = (msgIndex + 1) % loadingMessages.length;
        }
    }, 1500);
    
    window.portfolioLoadingInterval = portfolioLoadingInterval;
}

function hidePortfolioLoadingState() {
    const analyzeBtn = document.getElementById('analyzePortfolioBtn');
    const analyzeText = document.getElementById('analyzePortfolioText');
    const loadingOverlay = document.getElementById('portfolioLoadingOverlay');
    
    if (analyzeBtn) analyzeBtn.disabled = false;
    if (analyzeText) analyzeText.textContent = 'Analyze Portfolio';
    if (loadingOverlay) loadingOverlay.style.display = 'none';
    
    if (window.portfolioLoadingInterval) {
        clearInterval(window.portfolioLoadingInterval);
    }
}

function showPortfolioError(message) {
    console.error('Portfolio error:', message);
    // Could implement toast notification
}

/**
 * Update Portfolio Updates Feed
 */
function updatePortfolioUpdates(message) {
    const updatesContainer = document.getElementById('portfolioUpdates');
    if (!updatesContainer) return;
    
    const timestamp = new Date().toLocaleTimeString();
    
    const updateElement = document.createElement('div');
    updateElement.className = 'mb-2 p-2 rounded glass-effect fade-in';
    updateElement.innerHTML = `
        <small class="text-muted">${timestamp}</small><br>
        ${message}
    `;
    
    updatesContainer.insertBefore(updateElement, updatesContainer.firstChild);
    
    // Keep only last 10 updates
    while (updatesContainer.children.length > 10) {
        updatesContainer.removeChild(updatesContainer.lastChild);
    }
}

/**
 * Utility Functions
 */
function formatCurrency(value) {
    if (value >= 1e9) {
        return '$' + (value / 1e9).toFixed(2) + 'B';
    } else if (value >= 1e6) {
        return '$' + (value / 1e6).toFixed(2) + 'M';
    } else if (value >= 1e3) {
        return '$' + (value / 1e3).toFixed(2) + 'K';
    } else {
        return '$' + value.toFixed(2);
    }
}

// Export functions for global access
window.analyzePortfolio = analyzePortfolio;
window.initializePortfolioDashboard = initializePortfolioDashboard;