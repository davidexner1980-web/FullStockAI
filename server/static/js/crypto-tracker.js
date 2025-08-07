/**
 * CryptoTracker - Enhanced cryptocurrency tracking with real-time updates
 */

class CryptoTracker {
    constructor() {
        this.cryptoData = new Map();
        this.watchedCryptos = this.loadWatchedCryptos();
        this.updateInterval = null;
        this.sortOrder = { column: 'market_cap', direction: 'desc' };
        this.filters = { showFavorites: false, minVolume: 0 };
        
        this.init();
    }

    init() {
        console.log('CryptoTracker: Initializing...');
        
        this.setupEventListeners();
        this.loadCryptoData();
        this.startRealTimeUpdates();
        this.setupWebSocket();
    }

    setupEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('crypto-search');
        if (searchInput) {
            searchInput.addEventListener('input', (event) => {
                this.filterCryptos(event.target.value);
            });
        }

        // Sorting controls
        document.addEventListener('click', (event) => {
            if (event.target.closest('.sort-btn')) {
                const column = event.target.closest('.sort-btn').dataset.column;
                this.sortCryptos(column);
            }
        });

        // Filter controls
        const favoriteFilter = document.getElementById('filter-favorites');
        if (favoriteFilter) {
            favoriteFilter.addEventListener('change', (event) => {
                this.filters.showFavorites = event.target.checked;
                this.renderCryptoList();
            });
        }

        // Volume filter
        const volumeFilter = document.getElementById('min-volume');
        if (volumeFilter) {
            volumeFilter.addEventListener('input', (event) => {
                this.filters.minVolume = parseFloat(event.target.value) || 0;
                this.debounce(() => this.renderCryptoList(), 500)();
            });
        }

        // Refresh button
        const refreshBtn = document.getElementById('refresh-crypto');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshData();
            });
        }

        // Add to watchlist buttons
        document.addEventListener('click', (event) => {
            if (event.target.closest('.add-to-watchlist')) {
                const symbol = event.target.closest('.add-to-watchlist').dataset.symbol;
                this.toggleWatchlist(symbol);
            }
        });

        // Crypto detail buttons
        document.addEventListener('click', (event) => {
            if (event.target.closest('.crypto-detail')) {
                const symbol = event.target.closest('.crypto-detail').dataset.symbol;
                this.showCryptoDetail(symbol);
            }
        });

        // Prediction buttons
        document.addEventListener('click', (event) => {
            if (event.target.closest('.crypto-predict')) {
                const symbol = event.target.closest('.crypto-predict').dataset.symbol;
                this.getCryptoPrediction(symbol);
            }
        });
    }

    async loadCryptoData() {
        this.showLoadingState();
        
        try {
            // Load market overview
            const overview = await this.fetchMarketOverview();
            this.displayMarketOverview(overview);
            
            // Load top cryptocurrencies
            const topGainers = await this.fetchTopGainers();
            this.cryptoData.set('top_gainers', topGainers);
            
            // Load detailed data for major cryptos
            const majorCryptos = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOT', 'AVAX', 'LINK', 'MATIC', 'UNI'];
            await this.loadCryptoDetails(majorCryptos);
            
            this.renderCryptoList();
            
        } catch (error) {
            console.error('CryptoTracker: Failed to load data', error);
            this.showErrorState('Failed to load cryptocurrency data');
        } finally {
            this.hideLoadingState();
        }
    }

    async fetchMarketOverview() {
        try {
            const response = await fetch('/api/crypto/market_overview');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Market overview fetch failed:', error);
            return this.getDefaultMarketOverview();
        }
    }

    async fetchTopGainers() {
        try {
            const response = await fetch('/api/crypto/top_gainers');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Top gainers fetch failed:', error);
            return [];
        }
    }

    async loadCryptoDetails(symbols) {
        const promises = symbols.map(async (symbol) => {
            try {
                const prediction = await this.fetchCryptoPrediction(symbol);
                this.cryptoData.set(symbol, {
                    symbol: symbol,
                    ...prediction,
                    lastUpdated: Date.now()
                });
            } catch (error) {
                console.error(`Failed to load ${symbol}:`, error);
            }
        });
        
        await Promise.allSettled(promises);
    }

    async fetchCryptoPrediction(symbol) {
        const response = await fetch(`/api/crypto/predict/${symbol}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.json();
    }

    displayMarketOverview(overview) {
        const overviewContainer = document.getElementById('market-overview');
        if (!overviewContainer) return;

        const totalMarketCap = overview.total_market_cap || 'N/A';
        const totalVolume = overview.total_volume_24h || 'N/A';
        const bitcoinDominance = overview.bitcoin_dominance || 'N/A';
        const activeCryptos = overview.active_cryptocurrencies || 0;

        overviewContainer.innerHTML = `
            <div class="row g-3">
                <div class="col-6 col-md-3">
                    <div class="crypto-metric-card">
                        <div class="metric-icon">
                            <i data-feather="dollar-sign"></i>
                        </div>
                        <div class="metric-content">
                            <div class="metric-label">Market Cap</div>
                            <div class="metric-value">${totalMarketCap}</div>
                        </div>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="crypto-metric-card">
                        <div class="metric-icon">
                            <i data-feather="bar-chart-2"></i>
                        </div>
                        <div class="metric-content">
                            <div class="metric-label">24h Volume</div>
                            <div class="metric-value">${totalVolume}</div>
                        </div>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="crypto-metric-card">
                        <div class="metric-icon">
                            <i data-feather="pie-chart"></i>
                        </div>
                        <div class="metric-content">
                            <div class="metric-label">BTC Dominance</div>
                            <div class="metric-value">${bitcoinDominance}</div>
                        </div>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="crypto-metric-card">
                        <div class="metric-icon">
                            <i data-feather="trending-up"></i>
                        </div>
                        <div class="metric-content">
                            <div class="metric-label">Active Cryptos</div>
                            <div class="metric-value">${activeCryptos}</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Display top cryptos from overview
        if (overview.top_cryptos && overview.top_cryptos.length > 0) {
            this.displayTopCryptos(overview.top_cryptos);
        }

        // Refresh feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    displayTopCryptos(topCryptos) {
        const topCryptosContainer = document.getElementById('top-cryptos');
        if (!topCryptosContainer) return;

        const cryptosHtml = topCryptos.map(crypto => {
            const changeClass = crypto.change_24h > 0 ? 'text-success' : crypto.change_24h < 0 ? 'text-danger' : 'text-muted';
            const changeIcon = crypto.change_24h > 0 ? 'trending-up' : crypto.change_24h < 0 ? 'trending-down' : 'minus';
            
            return `
                <div class="col-6 col-md-4">
                    <div class="crypto-summary-card">
                        <div class="crypto-header">
                            <span class="crypto-symbol">${crypto.symbol}</span>
                            <button class="btn btn-sm btn-outline-primary add-to-watchlist" data-symbol="${crypto.symbol}">
                                <i data-feather="star"></i>
                            </button>
                        </div>
                        <div class="crypto-price">$${crypto.price.toFixed(2)}</div>
                        <div class="crypto-change ${changeClass}">
                            <i data-feather="${changeIcon}"></i>
                            ${crypto.change_24h > 0 ? '+' : ''}${crypto.change_24h.toFixed(2)}%
                        </div>
                        <button class="btn btn-sm btn-primary crypto-predict mt-2" data-symbol="${crypto.symbol}">
                            Get Prediction
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        topCryptosContainer.innerHTML = `
            <div class="row g-3">
                ${cryptosHtml}
            </div>
        `;

        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    renderCryptoList() {
        const listContainer = document.getElementById('crypto-list');
        if (!listContainer) return;

        let cryptos = Array.from(this.cryptoData.values()).filter(crypto => 
            crypto.symbol && crypto.current_price
        );

        // Apply filters
        if (this.filters.showFavorites) {
            cryptos = cryptos.filter(crypto => this.watchedCryptos.includes(crypto.symbol));
        }

        if (this.filters.minVolume > 0) {
            cryptos = cryptos.filter(crypto => (crypto.volume_24h || 0) >= this.filters.minVolume);
        }

        // Sort cryptos
        this.applySorting(cryptos);

        if (cryptos.length === 0) {
            listContainer.innerHTML = `
                <div class="text-center py-5">
                    <i data-feather="search" class="text-muted mb-3" style="width: 48px; height: 48px;"></i>
                    <h5 class="text-muted">No cryptocurrencies found</h5>
                    <p class="text-muted">Try adjusting your filters or search criteria</p>
                </div>
            `;
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
            return;
        }

        const cryptosHtml = cryptos.map(crypto => this.renderCryptoCard(crypto)).join('');
        
        listContainer.innerHTML = `
            <div class="row g-3">
                ${cryptosHtml}
            </div>
        `;

        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    renderCryptoCard(crypto) {
        const currentPrice = crypto.current_price || 0;
        const predictedPrice = crypto.prediction || 0;
        const change24h = crypto.price_change_24h || 0;
        const confidence = crypto.confidence || 0;
        const volume = crypto.volume_24h || 0;
        const marketCapRank = crypto.market_cap_rank || 999;
        
        const priceChange = predictedPrice > 0 ? ((predictedPrice - currentPrice) / currentPrice * 100) : 0;
        const changeClass = change24h > 0 ? 'text-success' : change24h < 0 ? 'text-danger' : 'text-muted';
        const predictionClass = priceChange > 0 ? 'text-success' : priceChange < 0 ? 'text-danger' : 'text-muted';
        const isWatched = this.watchedCryptos.includes(crypto.symbol);
        
        return `
            <div class="col-12 col-md-6 col-lg-4">
                <div class="crypto-card" data-symbol="${crypto.symbol}">
                    <div class="crypto-card-header">
                        <div class="crypto-info">
                            <h6 class="crypto-symbol">${crypto.symbol}</h6>
                            <span class="crypto-rank">#${marketCapRank}</span>
                        </div>
                        <button class="btn btn-sm ${isWatched ? 'btn-warning' : 'btn-outline-secondary'} add-to-watchlist" 
                                data-symbol="${crypto.symbol}">
                            <i data-feather="${isWatched ? 'star' : 'star'}"></i>
                        </button>
                    </div>
                    
                    <div class="crypto-price-section">
                        <div class="current-price">
                            <label>Current Price</label>
                            <div class="price">$${currentPrice.toFixed(2)}</div>
                        </div>
                        <div class="price-change ${changeClass}">
                            ${change24h > 0 ? '+' : ''}${change24h.toFixed(2)}%
                        </div>
                    </div>
                    
                    ${predictedPrice > 0 ? `
                        <div class="prediction-section">
                            <div class="predicted-price">
                                <label>AI Prediction</label>
                                <div class="price">$${predictedPrice.toFixed(2)}</div>
                            </div>
                            <div class="prediction-change ${predictionClass}">
                                ${priceChange > 0 ? '+' : ''}${priceChange.toFixed(2)}%
                            </div>
                        </div>
                        
                        <div class="confidence-section">
                            <label>Confidence: ${(confidence * 100).toFixed(1)}%</label>
                            <div class="progress">
                                <div class="progress-bar" style="width: ${confidence * 100}%"></div>
                            </div>
                        </div>
                    ` : ''}
                    
                    <div class="crypto-metrics">
                        <div class="metric">
                            <label>24h Volume</label>
                            <div class="value">${this.formatLargeNumber(volume)}</div>
                        </div>
                    </div>
                    
                    <div class="crypto-actions">
                        <button class="btn btn-sm btn-primary crypto-predict" data-symbol="${crypto.symbol}">
                            <i data-feather="trending-up"></i> ${predictedPrice > 0 ? 'Update' : 'Predict'}
                        </button>
                        <button class="btn btn-sm btn-outline-primary crypto-detail" data-symbol="${crypto.symbol}">
                            <i data-feather="info"></i> Details
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    sortCryptos(column) {
        if (this.sortOrder.column === column) {
            this.sortOrder.direction = this.sortOrder.direction === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortOrder.column = column;
            this.sortOrder.direction = 'desc';
        }
        
        this.renderCryptoList();
        this.updateSortButtons();
    }

    applySorting(cryptos) {
        const { column, direction } = this.sortOrder;
        
        cryptos.sort((a, b) => {
            let aVal = a[column] || 0;
            let bVal = b[column] || 0;
            
            // Handle special sorting cases
            if (column === 'symbol') {
                aVal = aVal.toString();
                bVal = bVal.toString();
            }
            
            if (direction === 'asc') {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });
    }

    updateSortButtons() {
        const sortButtons = document.querySelectorAll('.sort-btn');
        sortButtons.forEach(btn => {
            const column = btn.dataset.column;
            btn.classList.remove('active', 'asc', 'desc');
            
            if (column === this.sortOrder.column) {
                btn.classList.add('active', this.sortOrder.direction);
            }
        });
    }

    filterCryptos(query) {
        const searchTerm = query.toLowerCase().trim();
        const cryptoCards = document.querySelectorAll('.crypto-card');
        
        cryptoCards.forEach(card => {
            const symbol = card.dataset.symbol.toLowerCase();
            const shouldShow = symbol.includes(searchTerm);
            
            card.closest('.col-12, .col-md-6, .col-lg-4').style.display = shouldShow ? 'block' : 'none';
        });
    }

    async getCryptoPrediction(symbol) {
        const button = document.querySelector(`.crypto-predict[data-symbol="${symbol}"]`);
        if (button) {
            button.innerHTML = '<i data-feather="loader"></i> Loading...';
            button.disabled = true;
        }
        
        try {
            const prediction = await this.fetchCryptoPrediction(symbol);
            
            // Update the stored data
            this.cryptoData.set(symbol, {
                ...this.cryptoData.get(symbol),
                ...prediction,
                lastUpdated: Date.now()
            });
            
            // Re-render the list to show updated prediction
            this.renderCryptoList();
            
            // Show success message
            if (window.app) {
                window.app.showSuccessMessage(`${symbol} prediction updated`);
            }
            
        } catch (error) {
            console.error(`Prediction failed for ${symbol}:`, error);
            if (window.app) {
                window.app.showErrorMessage(`Failed to get ${symbol} prediction`, error.message);
            }
        } finally {
            if (button) {
                button.innerHTML = '<i data-feather="trending-up"></i> Predict';
                button.disabled = false;
                if (typeof feather !== 'undefined') {
                    feather.replace();
                }
            }
        }
    }

    showCryptoDetail(symbol) {
        const crypto = this.cryptoData.get(symbol);
        if (!crypto) {
            if (window.app) {
                window.app.showErrorMessage('Crypto data not available');
            }
            return;
        }

        // Create and show detail modal
        const modalHtml = `
            <div class="modal fade" id="cryptoDetailModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${symbol} Detailed Analysis</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${this.renderCryptoDetailContent(crypto)}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" onclick="cryptoTracker.getCryptoPrediction('${symbol}')">
                                Update Prediction
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        const existingModal = document.getElementById('cryptoDetailModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add new modal to DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('cryptoDetailModal'));
        modal.show();

        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    renderCryptoDetailContent(crypto) {
        const currentPrice = crypto.current_price || 0;
        const predictedPrice = crypto.prediction || 0;
        const confidence = crypto.confidence || 0;
        const change24h = crypto.price_change_24h || 0;
        const volume24h = crypto.volume_24h || 0;
        const marketCapRank = crypto.market_cap_rank || 999;
        
        const priceChange = predictedPrice > 0 ? ((predictedPrice - currentPrice) / currentPrice * 100) : 0;
        const topFeatures = crypto.top_features || [];

        return `
            <div class="crypto-detail-content">
                <div class="row mb-4">
                    <div class="col-md-6">
                        <div class="detail-card">
                            <h6>Current Market Data</h6>
                            <div class="detail-metrics">
                                <div class="metric-row">
                                    <span>Price:</span>
                                    <span class="fw-bold">$${currentPrice.toFixed(2)}</span>
                                </div>
                                <div class="metric-row">
                                    <span>24h Change:</span>
                                    <span class="${change24h >= 0 ? 'text-success' : 'text-danger'} fw-bold">
                                        ${change24h > 0 ? '+' : ''}${change24h.toFixed(2)}%
                                    </span>
                                </div>
                                <div class="metric-row">
                                    <span>24h Volume:</span>
                                    <span class="fw-bold">${this.formatLargeNumber(volume24h)}</span>
                                </div>
                                <div class="metric-row">
                                    <span>Market Rank:</span>
                                    <span class="fw-bold">#${marketCapRank}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="detail-card">
                            <h6>AI Prediction</h6>
                            ${predictedPrice > 0 ? `
                                <div class="detail-metrics">
                                    <div class="metric-row">
                                        <span>Predicted Price:</span>
                                        <span class="fw-bold">$${predictedPrice.toFixed(2)}</span>
                                    </div>
                                    <div class="metric-row">
                                        <span>Expected Change:</span>
                                        <span class="${priceChange >= 0 ? 'text-success' : 'text-danger'} fw-bold">
                                            ${priceChange > 0 ? '+' : ''}${priceChange.toFixed(2)}%
                                        </span>
                                    </div>
                                    <div class="metric-row">
                                        <span>Confidence:</span>
                                        <span class="fw-bold">${(confidence * 100).toFixed(1)}%</span>
                                    </div>
                                    <div class="confidence-bar mt-2">
                                        <div class="progress">
                                            <div class="progress-bar" style="width: ${confidence * 100}%"></div>
                                        </div>
                                    </div>
                                </div>
                            ` : `
                                <p class="text-muted">No prediction available. Click "Update Prediction" to generate one.</p>
                            `}
                        </div>
                    </div>
                </div>
                
                ${topFeatures.length > 0 ? `
                    <div class="row">
                        <div class="col-12">
                            <div class="detail-card">
                                <h6>Key Factors</h6>
                                <div class="feature-list">
                                    ${topFeatures.map(feature => `
                                        <div class="feature-item">
                                            <span class="feature-name">${feature.feature}</span>
                                            <span class="feature-importance">${(feature.importance * 100).toFixed(1)}%</span>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                    </div>
                ` : ''}
                
                <div class="row mt-3">
                    <div class="col-12">
                        <div class="detail-card">
                            <h6>Trading Signal</h6>
                            <div class="signal-section">
                                <span class="badge bg-${crypto.signal === 'BUY' ? 'success' : crypto.signal === 'SELL' ? 'danger' : 'warning'} signal-badge">
                                    ${crypto.signal || 'HOLD'}
                                </span>
                                ${crypto.volatility_warning ? `
                                    <div class="alert alert-warning mt-2 mb-0">
                                        <i data-feather="alert-triangle"></i>
                                        High volatility detected. Exercise caution when trading.
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    toggleWatchlist(symbol) {
        const isWatched = this.watchedCryptos.includes(symbol);
        
        if (isWatched) {
            this.watchedCryptos = this.watchedCryptos.filter(s => s !== symbol);
            if (window.app) {
                window.app.showSuccessMessage(`${symbol} removed from watchlist`);
            }
        } else {
            this.watchedCryptos.push(symbol);
            if (window.app) {
                window.app.showSuccessMessage(`${symbol} added to watchlist`);
            }
        }
        
        this.saveWatchedCryptos();
        this.renderCryptoList();
    }

    startRealTimeUpdates() {
        // Update data every 30 seconds
        this.updateInterval = setInterval(() => {
            if (document.visibilityState === 'visible' && navigator.onLine) {
                this.refreshPrices();
            }
        }, 30000);
    }

    async refreshPrices() {
        try {
            // Refresh data for watched cryptos
            const watchedPromises = this.watchedCryptos.map(async (symbol) => {
                try {
                    const prediction = await this.fetchCryptoPrediction(symbol);
                    this.cryptoData.set(symbol, {
                        ...this.cryptoData.get(symbol),
                        ...prediction,
                        lastUpdated: Date.now()
                    });
                } catch (error) {
                    console.warn(`Failed to refresh ${symbol}:`, error);
                }
            });
            
            await Promise.allSettled(watchedPromises);
            this.renderCryptoList();
            
        } catch (error) {
            console.error('Price refresh failed:', error);
        }
    }

    setupWebSocket() {
        if (window.WebSocketClient) {
            this.ws = new WebSocketClient();
            this.ws.on('crypto_price_update', (data) => {
                this.handlePriceUpdate(data);
            });
        }
    }

    handlePriceUpdate(data) {
        const { symbol, price, change } = data;
        const crypto = this.cryptoData.get(symbol);
        
        if (crypto) {
            crypto.current_price = price;
            crypto.price_change_24h = change;
            crypto.lastUpdated = Date.now();
            
            // Update the specific card without full re-render
            this.updateCryptoCard(symbol);
        }
    }

    updateCryptoCard(symbol) {
        const card = document.querySelector(`.crypto-card[data-symbol="${symbol}"]`);
        if (card) {
            const crypto = this.cryptoData.get(symbol);
            const priceElement = card.querySelector('.current-price .price');
            const changeElement = card.querySelector('.price-change');
            
            if (priceElement && crypto) {
                priceElement.textContent = `$${crypto.current_price.toFixed(2)}`;
                
                if (changeElement) {
                    const change = crypto.price_change_24h || 0;
                    const changeClass = change > 0 ? 'text-success' : change < 0 ? 'text-danger' : 'text-muted';
                    changeElement.className = `price-change ${changeClass}`;
                    changeElement.textContent = `${change > 0 ? '+' : ''}${change.toFixed(2)}%`;
                }
            }
        }
    }

    async refreshData() {
        const refreshBtn = document.getElementById('refresh-crypto');
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i data-feather="loader"></i> Refreshing...';
            refreshBtn.disabled = true;
        }
        
        try {
            await this.loadCryptoData();
            if (window.app) {
                window.app.showSuccessMessage('Crypto data refreshed');
            }
        } catch (error) {
            console.error('Refresh failed:', error);
            if (window.app) {
                window.app.showErrorMessage('Failed to refresh data', error.message);
            }
        } finally {
            if (refreshBtn) {
                refreshBtn.innerHTML = '<i data-feather="refresh-cw"></i> Refresh';
                refreshBtn.disabled = false;
                if (typeof feather !== 'undefined') {
                    feather.replace();
                }
            }
        }
    }

    // Utility methods
    formatLargeNumber(num) {
        if (num >= 1e9) {
            return (num / 1e9).toFixed(2) + 'B';
        } else if (num >= 1e6) {
            return (num / 1e6).toFixed(2) + 'M';
        } else if (num >= 1e3) {
            return (num / 1e3).toFixed(2) + 'K';
        }
        return num.toFixed(2);
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    loadWatchedCryptos() {
        try {
            return JSON.parse(localStorage.getItem('watched-cryptos') || '[]');
        } catch {
            return [];
        }
    }

    saveWatchedCryptos() {
        localStorage.setItem('watched-cryptos', JSON.stringify(this.watchedCryptos));
    }

    getDefaultMarketOverview() {
        return {
            total_market_cap: 'N/A',
            total_volume_24h: 'N/A',
            bitcoin_dominance: 'N/A',
            active_cryptocurrencies: 0,
            top_cryptos: []
        };
    }

    showLoadingState() {
        const containers = ['market-overview', 'top-cryptos', 'crypto-list'];
        containers.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.innerHTML = `
                    <div class="loading-state text-center py-5">
                        <div class="spinner-border text-primary mb-3"></div>
                        <p class="text-muted">Loading cryptocurrency data...</p>
                    </div>
                `;
            }
        });
    }

    hideLoadingState() {
        // Loading states will be replaced by actual content
    }

    showErrorState(message) {
        const containers = ['market-overview', 'top-cryptos', 'crypto-list'];
        containers.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.innerHTML = `
                    <div class="error-state text-center py-5">
                        <i data-feather="alert-circle" class="text-danger mb-3" style="width: 48px; height: 48px;"></i>
                        <h5 class="text-danger">Error Loading Data</h5>
                        <p class="text-muted">${message}</p>
                        <button class="btn btn-primary" onclick="cryptoTracker.refreshData()">
                            <i data-feather="refresh-cw"></i> Try Again
                        </button>
                    </div>
                `;
            }
        });
        
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        if (this.ws) {
            this.ws.disconnect();
        }
    }
}

// Initialize crypto tracker when page loads
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname === '/crypto') {
        window.cryptoTracker = new CryptoTracker();
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CryptoTracker;
}
