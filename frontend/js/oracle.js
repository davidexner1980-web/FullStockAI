/**
 * FullStock AI Oracle Dashboard - Mystical Market Insights
 * Handles oracle consultations, dreams, and mystical market analysis
 */

let currentOracleMode = 'vision';
let currentOracleSymbol = 'SPY';
let isConsultingOracle = false;

/**
 * Initialize Oracle Dashboard
 */
function initializeOracleDashboard() {
    console.log('Oracle Dashboard initialized - mystical forces activated');
    
    // Setup event listeners
    setupOracleEventListeners();
    
    // Initialize WebSocket connection
    if (typeof initializeWebSocket === 'function') {
        initializeWebSocket();
    }
    
    // Start ambient oracle effects
    startOracleEffects();
}

/**
 * Setup Oracle Event Listeners
 */
function setupOracleEventListeners() {
    const consultBtn = document.getElementById('consultOracleBtn');
    const oracleInput = document.getElementById('oracleInput');
    const oracleModes = document.querySelectorAll('.oracle-mode');

    // Consult Oracle button
    if (consultBtn) {
        consultBtn.addEventListener('click', () => {
            const symbol = oracleInput.value.trim().toUpperCase();
            if (symbol) {
                consultOracle(symbol, currentOracleMode);
            }
        });
    }

    // Enter key in input
    if (oracleInput) {
        oracleInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const symbol = oracleInput.value.trim().toUpperCase();
                if (symbol) {
                    consultOracle(symbol, currentOracleMode);
                }
            }
        });
    }

    // Oracle mode buttons
    oracleModes.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state
            oracleModes.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update current mode
            currentOracleMode = btn.getAttribute('data-mode');
            console.log('Oracle mode changed to:', currentOracleMode);
        });
    });
}

/**
 * Consult Oracle - Main Function
 */
async function consultOracle(symbol, mode = 'vision') {
    if (isConsultingOracle) return;
    
    console.log(`Consulting Oracle for ${symbol} in ${mode} mode...`);
    isConsultingOracle = true;
    currentOracleSymbol = symbol;
    
    // Update UI state
    showOracleLoadingState();
    
    try {
        // Fetch oracle insights from backend
        const response = await fetch(`/api/oracle/${symbol}?mode=${mode}`);
        
        if (!response.ok) {
            throw new Error(`Oracle API Error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Oracle consultation successful:', data);
        
        // Update UI with mystical insights
        updateOracleDisplay(data, mode);
        addOracleToHistory(symbol, mode, data);
        
        // Show oracle sections
        showOracleResultSections();
        
        // Fetch additional mystical data
        await fetchAdditionalOracleData(symbol);
        
    } catch (error) {
        console.error('Oracle consultation error:', error);
        showOracleError(`The Oracle is clouded: ${error.message}`);
    } finally {
        hideOracleLoadingState();
        isConsultingOracle = false;
    }
}

/**
 * Update Oracle Display with Mystical Data
 */
function updateOracleDisplay(data, mode) {
    console.log('Updating Oracle display:', data);
    
    // Update main oracle panel
    const symbols = {
        vision: '👁️',
        dreams: '💭', 
        prophecy: '🔮',
        wisdom: '📜'
    };
    
    document.getElementById('oracleSymbol').textContent = symbols[mode] || '🔮';
    
    // Update oracle title and message
    if (data.title) {
        document.getElementById('oracleTitle').textContent = data.title;
    }
    
    if (data.message) {
        document.getElementById('oracleMessage').textContent = data.message;
    } else if (data.insight) {
        document.getElementById('oracleMessage').textContent = data.insight;
    }
    
    // Update market consciousness
    if (data.consciousness_level !== undefined) {
        const consciousnessPercent = (data.consciousness_level * 100).toFixed(0);
        document.getElementById('consciousnessLevel').textContent = `${consciousnessPercent}%`;
        
        if (data.consciousness_insight) {
            document.getElementById('consciousnessInsight').innerHTML = `<p>${data.consciousness_insight}</p>`;
        }
    }
    
    // Update mystical indicators
    if (data.mystical_indicators) {
        updateMysticalIndicators(data.mystical_indicators);
    }
    
    // Update oracle dreams if available
    if (data.dreams && Array.isArray(data.dreams)) {
        updateOracleDreams(data.dreams);
    }
}

/**
 * Update Mystical Indicators
 */
function updateMysticalIndicators(indicators) {
    console.log('Updating mystical indicators:', indicators);
    
    if (indicators.lunar_phase) {
        document.getElementById('lunarPhase').textContent = indicators.lunar_phase;
    }
    
    if (indicators.market_harmony !== undefined) {
        const harmony = (indicators.market_harmony * 100).toFixed(0);
        document.getElementById('marketHarmony').textContent = `${harmony}%`;
        
        // Color coding
        const harmonyElement = document.getElementById('marketHarmony');
        if (harmony < 30) {
            harmonyElement.className = 'sentiment-negative';
        } else if (harmony > 70) {
            harmonyElement.className = 'sentiment-positive';
        } else {
            harmonyElement.className = 'sentiment-neutral';
        }
    }
    
    if (indicators.volatility_aura) {
        document.getElementById('volatilityAura').textContent = indicators.volatility_aura;
    }
    
    if (indicators.profit_resonance) {
        document.getElementById('profitResonance').textContent = indicators.profit_resonance;
    }
}

/**
 * Update Oracle Dreams
 */
function updateOracleDreams(dreams) {
    console.log('Updating oracle dreams:', dreams);
    
    const dreamSymbols = ['🌟', '🔥', '💎', '⚡', '🌙', '✨'];
    
    dreams.forEach((dream, index) => {
        if (index < 3) { // Only update first 3 dream cards
            const symbolElement = document.getElementById(`dreamSymbol${index + 1}`);
            const titleElement = document.getElementById(`dreamTitle${index + 1}`);
            const textElement = document.getElementById(`dreamText${index + 1}`);
            
            if (symbolElement) {
                symbolElement.textContent = dream.symbol || dreamSymbols[index];
            }
            
            if (titleElement) {
                titleElement.textContent = dream.title || `Vision ${index + 1}`;
            }
            
            if (textElement) {
                textElement.textContent = dream.message || dream.interpretation || 'Mystical vision awaits interpretation...';
            }
        }
    });
}

/**
 * Fetch Additional Oracle Data
 */
async function fetchAdditionalOracleData(symbol) {
    try {
        // Fetch curiosity engine alerts
        const curiosityResponse = await fetch(`/api/curiosity/${symbol}`);
        if (curiosityResponse.ok) {
            const curiosityData = await curiosityResponse.json();
            updateCuriosityAlerts(curiosityData);
        }
        
        // Fetch quantum forecasts
        const quantumResponse = await fetch(`/api/quantum_forecast/${symbol}`);
        if (quantumResponse.ok) {
            const quantumData = await quantumResponse.json();
            updateQuantumForecasts(quantumData);
        }
        
    } catch (error) {
        console.log('Additional oracle data fetch failed:', error);
    }
}

/**
 * Update Curiosity Engine Alerts
 */
function updateCuriosityAlerts(data) {
    const alertsContainer = document.getElementById('curiosityAlerts');
    if (!alertsContainer) return;
    
    if (data.alerts && data.alerts.length > 0) {
        alertsContainer.innerHTML = '';
        
        data.alerts.forEach(alert => {
            const alertElement = document.createElement('div');
            alertElement.className = 'mb-2 p-2 rounded glass-effect';
            
            const severity = alert.severity || 'info';
            const icon = severity === 'high' ? '🚨' : severity === 'medium' ? '⚠️' : 'ℹ️';
            
            alertElement.innerHTML = `
                <div class="d-flex align-items-start">
                    <div class="me-2">${icon}</div>
                    <div>
                        <small class="text-muted">${new Date(alert.timestamp || Date.now()).toLocaleTimeString()}</small><br>
                        <strong>${alert.title || 'Anomaly Detected'}</strong><br>
                        <span class="text-muted">${alert.description || alert.message}</span>
                    </div>
                </div>
            `;
            
            alertsContainer.appendChild(alertElement);
        });
    } else {
        alertsContainer.innerHTML = '<p class="text-muted text-center">No anomalies detected</p>';
    }
}

/**
 * Update Quantum Forecasts
 */
function updateQuantumForecasts(data) {
    const forecastsContainer = document.getElementById('quantumForecasts');
    if (!forecastsContainer) return;
    
    if (data.forecasts && data.forecasts.length > 0) {
        forecastsContainer.innerHTML = '';
        
        data.forecasts.forEach(forecast => {
            const forecastElement = document.createElement('div');
            forecastElement.className = 'mb-2 p-2 rounded glass-effect';
            
            const confidence = forecast.confidence || 0;
            const confidencePercent = (confidence * 100).toFixed(0);
            
            forecastElement.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <strong>${forecast.timeframe || 'Short Term'}</strong>
                    <span class="badge bg-secondary">${confidencePercent}%</span>
                </div>
                <p class="text-muted mb-0">${forecast.prediction || forecast.message}</p>
            `;
            
            forecastsContainer.appendChild(forecastElement);
        });
    } else {
        forecastsContainer.innerHTML = '<p class="text-muted text-center">Analyzing quantum patterns...</p>';
    }
}

/**
 * Add Oracle Consultation to History
 */
function addOracleToHistory(symbol, mode, data) {
    const historyContainer = document.getElementById('oracleHistory');
    if (!historyContainer) return;
    
    const timestamp = new Date().toLocaleString();
    
    const historyElement = document.createElement('div');
    historyElement.className = 'mb-2 p-2 rounded glass-effect fade-in';
    
    const modeEmojis = {
        vision: '👁️',
        dreams: '💭',
        prophecy: '🔮',
        wisdom: '📜'
    };
    
    historyElement.innerHTML = `
        <div class="d-flex align-items-start">
            <div class="me-2">${modeEmojis[mode] || '🔮'}</div>
            <div class="flex-grow-1">
                <div class="d-flex justify-content-between">
                    <strong>${symbol}</strong>
                    <small class="text-muted">${timestamp}</small>
                </div>
                <small class="text-muted text-capitalize">${mode} Consultation</small><br>
                <span class="text-truncate d-block">${data.message || data.insight || 'Oracle guidance received'}</span>
            </div>
        </div>
    `;
    
    // Insert at top
    historyContainer.insertBefore(historyElement, historyContainer.firstChild);
    
    // Keep only last 10 consultations
    while (historyContainer.children.length > 10) {
        historyContainer.removeChild(historyContainer.lastChild);
    }
}

/**
 * Start Oracle Ambient Effects
 */
function startOracleEffects() {
    // Add subtle animations and effects
    const oracleSymbols = document.querySelectorAll('.oracle-symbol');
    
    oracleSymbols.forEach(symbol => {
        symbol.addEventListener('mouseenter', () => {
            symbol.style.transform = 'scale(1.1) rotate(5deg)';
            symbol.style.transition = 'transform 0.3s ease';
        });
        
        symbol.addEventListener('mouseleave', () => {
            symbol.style.transform = 'scale(1) rotate(0deg)';
        });
    });
    
    // Periodic oracle updates (every 5 minutes)
    setInterval(() => {
        if (currentOracleSymbol && !isConsultingOracle) {
            // Fetch updated mystical indicators silently
            fetch(`/api/oracle/${currentOracleSymbol}?mode=${currentOracleMode}&update=true`)
                .then(response => response.json())
                .then(data => {
                    if (data.mystical_indicators) {
                        updateMysticalIndicators(data.mystical_indicators);
                    }
                })
                .catch(error => console.log('Silent oracle update failed:', error));
        }
    }, 300000); // 5 minutes
}

/**
 * Show/Hide Oracle UI Sections
 */
function showOracleResultSections() {
    document.getElementById('oracleMainPanel').style.display = 'block';
    document.getElementById('oracleInsightsSection').style.display = 'block';
    document.getElementById('oracleDreamsSection').style.display = 'block';
}

function showOracleLoadingState() {
    const consultBtn = document.getElementById('consultOracleBtn');
    const consultText = document.getElementById('consultText');
    const loadingOverlay = document.getElementById('oracleLoadingOverlay');
    
    if (consultBtn) consultBtn.disabled = true;
    if (consultText) consultText.textContent = 'Consulting...';
    if (loadingOverlay) loadingOverlay.style.display = 'flex';
    
    // Update loading text periodically
    const mysticalMessages = [
        'Channeling mystical market forces...',
        'Reading the cosmic patterns...',
        'Interpreting ancient market wisdom...',
        'Consulting the oracle spirits...',
        'Aligning with market consciousness...'
    ];
    
    let msgIndex = 0;
    const oracleLoadingInterval = setInterval(() => {
        const loadingTextElement = document.getElementById('oracleLoadingText');
        if (loadingTextElement) {
            loadingTextElement.textContent = mysticalMessages[msgIndex];
            msgIndex = (msgIndex + 1) % mysticalMessages.length;
        }
    }, 2000);
    
    window.oracleLoadingInterval = oracleLoadingInterval;
}

function hideOracleLoadingState() {
    const consultBtn = document.getElementById('consultOracleBtn');
    const consultText = document.getElementById('consultText');
    const loadingOverlay = document.getElementById('oracleLoadingOverlay');
    
    if (consultBtn) consultBtn.disabled = false;
    if (consultText) consultText.textContent = 'Consult Oracle';
    if (loadingOverlay) loadingOverlay.style.display = 'none';
    
    if (window.oracleLoadingInterval) {
        clearInterval(window.oracleLoadingInterval);
    }
}

function showOracleError(message) {
    createToast(message, 'error');

    // Update main oracle panel with error message
    document.getElementById('oracleSymbol').textContent = '🌫️';
    document.getElementById('oracleTitle').textContent = 'Oracle Vision Clouded';
    document.getElementById('oracleMessage').textContent = message;
    
    // Show the panel even with error
    document.getElementById('oracleMainPanel').style.display = 'block';
}

/**
 * Update Oracle Panel (for WebSocket updates)
 */
function updateOraclePanel(data) {
    if (typeof updateOracleDisplay === 'function') {
        updateOracleDisplay(data, currentOracleMode);
    }
}

// Export functions for global access
window.consultOracle = consultOracle;
window.initializeOracleDashboard = initializeOracleDashboard;
window.updateOraclePanel = updateOraclePanel;
