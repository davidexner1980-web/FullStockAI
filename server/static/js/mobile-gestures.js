/**
 * MobileGestures - Touch gesture handling for mobile PWA
 */

class MobileGestures {
    constructor() {
        this.isEnabled = this.isTouchDevice();
        this.gestures = new Map();
        this.swipeThreshold = 50;
        this.tapTimeout = 300;
        this.longPressTimeout = 500;
        this.pinchThreshold = 20;
        
        if (this.isEnabled) {
            this.init();
        }
    }

    init() {
        console.log('MobileGestures: Initializing touch gestures...');
        
        this.setupSwipeGestures();
        this.setupTapGestures();
        this.setupPinchGestures();
        this.setupPullToRefresh();
        this.setupHapticFeedback();
        
        // Prevent default touch behaviors that interfere with gestures
        this.preventDefaults();
    }

    isTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }

    setupSwipeGestures() {
        let startX = 0;
        let startY = 0;
        let startTime = 0;

        document.addEventListener('touchstart', (event) => {
            if (event.touches.length === 1) {
                const touch = event.touches[0];
                startX = touch.clientX;
                startY = touch.clientY;
                startTime = Date.now();
            }
        }, { passive: true });

        document.addEventListener('touchend', (event) => {
            if (event.changedTouches.length === 1) {
                const touch = event.changedTouches[0];
                const endX = touch.clientX;
                const endY = touch.clientY;
                const endTime = Date.now();

                const deltaX = endX - startX;
                const deltaY = endY - startY;
                const deltaTime = endTime - startTime;

                // Check if it's a swipe (fast movement)
                if (deltaTime < 300 && (Math.abs(deltaX) > this.swipeThreshold || Math.abs(deltaY) > this.swipeThreshold)) {
                    this.handleSwipe(deltaX, deltaY, event.target);
                }
            }
        }, { passive: true });
    }

    handleSwipe(deltaX, deltaY, target) {
        const absX = Math.abs(deltaX);
        const absY = Math.abs(deltaY);
        
        // Determine swipe direction
        let direction;
        if (absX > absY) {
            direction = deltaX > 0 ? 'right' : 'left';
        } else {
            direction = deltaY > 0 ? 'down' : 'up';
        }

        console.log(`Swipe detected: ${direction}`);
        
        // Handle specific swipe actions
        this.processSwipeAction(direction, target);
        
        // Trigger haptic feedback
        this.triggerHaptic('light');
    }

    processSwipeAction(direction, target) {
        // Navigation swipes
        if (direction === 'right' && this.isAtLeftEdge()) {
            this.handleBackNavigation();
        }
        
        // Card actions
        const card = target.closest('.crypto-card, .holding-card, .prediction-card');
        if (card) {
            this.handleCardSwipe(card, direction);
        }
        
        // List item actions
        const listItem = target.closest('.watchlist-item, .alert-item');
        if (listItem) {
            this.handleListItemSwipe(listItem, direction);
        }
        
        // Chart navigation
        const chartContainer = target.closest('.chart-container');
        if (chartContainer) {
            this.handleChartSwipe(chartContainer, direction);
        }
    }

    handleBackNavigation() {
        if (window.history.length > 1) {
            window.history.back();
        }
    }

    handleCardSwipe(card, direction) {
        const symbol = card.dataset.symbol;
        
        if (direction === 'left') {
            // Add to watchlist
            if (window.app && symbol) {
                window.app.addToWatchlist(symbol);
                this.showSwipeAction(card, 'Added to watchlist', 'success');
            }
        } else if (direction === 'right') {
            // Show quick actions
            this.showQuickActions(card);
        }
    }

    handleListItemSwipe(item, direction) {
        if (direction === 'left') {
            // Delete action
            this.showDeleteAction(item);
        } else if (direction === 'right') {
            // Edit action
            this.showEditAction(item);
        }
    }

    handleChartSwipe(container, direction) {
        if (direction === 'left' || direction === 'right') {
            // Change time period
            this.changeChartPeriod(container, direction);
        }
    }

    setupTapGestures() {
        let tapTimeout;
        let lastTap = 0;

        document.addEventListener('touchstart', (event) => {
            const now = Date.now();
            const timeBetweenTaps = now - lastTap;
            
            if (timeBetweenTaps < this.tapTimeout && timeBetweenTaps > 0) {
                // Double tap detected
                this.handleDoubleTap(event);
                event.preventDefault();
            } else {
                // Single tap - wait to see if double tap follows
                tapTimeout = setTimeout(() => {
                    this.handleSingleTap(event);
                }, this.tapTimeout);
            }
            
            lastTap = now;
        }, { passive: false });

        // Long press detection
        let longPressTimer;
        let longPressStarted = false;

        document.addEventListener('touchstart', (event) => {
            longPressStarted = true;
            longPressTimer = setTimeout(() => {
                if (longPressStarted) {
                    this.handleLongPress(event);
                }
            }, this.longPressTimeout);
        }, { passive: true });

        document.addEventListener('touchmove', () => {
            longPressStarted = false;
            clearTimeout(longPressTimer);
        }, { passive: true });

        document.addEventListener('touchend', () => {
            longPressStarted = false;
            clearTimeout(longPressTimer);
        }, { passive: true });
    }

    handleSingleTap(event) {
        const target = event.target;
        
        // Handle interactive elements
        if (target.closest('.tap-to-expand')) {
            this.toggleExpansion(target.closest('.tap-to-expand'));
        }
        
        if (target.closest('.metric-card')) {
            this.showMetricDetails(target.closest('.metric-card'));
        }
    }

    handleDoubleTap(event) {
        const target = event.target;
        
        // Quick actions on double tap
        const card = target.closest('.crypto-card, .stock-card');
        if (card) {
            this.quickPrediction(card);
        }
        
        // Chart zoom
        const chart = target.closest('.chart-container');
        if (chart) {
            this.toggleChartZoom(chart);
        }
        
        this.triggerHaptic('medium');
    }

    handleLongPress(event) {
        const target = event.target.closest('[data-long-press]');
        if (target) {
            const action = target.dataset.longPress;
            this.executeLongPressAction(action, target);
            this.triggerHaptic('heavy');
        }
    }

    setupPinchGestures() {
        let initialDistance = 0;
        let lastScale = 1;

        document.addEventListener('touchstart', (event) => {
            if (event.touches.length === 2) {
                initialDistance = this.getDistance(event.touches[0], event.touches[1]);
            }
        }, { passive: true });

        document.addEventListener('touchmove', (event) => {
            if (event.touches.length === 2) {
                const currentDistance = this.getDistance(event.touches[0], event.touches[1]);
                const scale = currentDistance / initialDistance;
                
                if (Math.abs(scale - lastScale) > 0.1) {
                    this.handlePinch(scale, event);
                    lastScale = scale;
                }
            }
        }, { passive: true });
    }

    getDistance(touch1, touch2) {
        const dx = touch1.clientX - touch2.clientX;
        const dy = touch1.clientY - touch2.clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }

    handlePinch(scale, event) {
        const target = event.target.closest('.chart-container, .zoomable');
        if (target) {
            if (scale > 1.1) {
                this.zoomIn(target);
            } else if (scale < 0.9) {
                this.zoomOut(target);
            }
        }
    }

    setupPullToRefresh() {
        let startY = 0;
        let currentY = 0;
        let isRefreshing = false;
        let pullDistance = 0;
        const pullThreshold = 100;

        const refreshIndicator = this.createRefreshIndicator();

        document.addEventListener('touchstart', (event) => {
            if (window.scrollY === 0 && event.touches.length === 1) {
                startY = event.touches[0].clientY;
            }
        }, { passive: true });

        document.addEventListener('touchmove', (event) => {
            if (startY > 0 && window.scrollY === 0 && event.touches.length === 1) {
                currentY = event.touches[0].clientY;
                pullDistance = currentY - startY;

                if (pullDistance > 0) {
                    event.preventDefault();
                    this.updateRefreshIndicator(refreshIndicator, pullDistance, pullThreshold);
                }
            }
        }, { passive: false });

        document.addEventListener('touchend', () => {
            if (pullDistance > pullThreshold && !isRefreshing) {
                isRefreshing = true;
                this.executeRefresh(refreshIndicator).then(() => {
                    isRefreshing = false;
                    pullDistance = 0;
                });
            } else {
                this.hideRefreshIndicator(refreshIndicator);
            }
            
            startY = 0;
            pullDistance = 0;
        }, { passive: true });
    }

    createRefreshIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'pull-refresh-indicator';
        indicator.innerHTML = `
            <div class="refresh-spinner">
                <i data-feather="refresh-cw"></i>
            </div>
            <div class="refresh-text">Pull to refresh</div>
        `;
        
        document.body.appendChild(indicator);
        return indicator;
    }

    updateRefreshIndicator(indicator, distance, threshold) {
        const progress = Math.min(distance / threshold, 1);
        indicator.style.transform = `translateY(${Math.min(distance * 0.5, 50)}px)`;
        indicator.style.opacity = progress;
        
        if (progress >= 1) {
            indicator.querySelector('.refresh-text').textContent = 'Release to refresh';
            indicator.classList.add('ready');
        } else {
            indicator.querySelector('.refresh-text').textContent = 'Pull to refresh';
            indicator.classList.remove('ready');
        }
    }

    async executeRefresh(indicator) {
        indicator.classList.add('refreshing');
        indicator.querySelector('.refresh-text').textContent = 'Refreshing...';
        
        try {
            // Trigger refresh based on current page
            if (window.app) {
                await window.app.refreshCurrentPageData();
            }
            
            this.triggerHaptic('light');
            
            setTimeout(() => {
                this.hideRefreshIndicator(indicator);
            }, 1000);
            
        } catch (error) {
            console.error('Refresh failed:', error);
            this.hideRefreshIndicator(indicator);
        }
    }

    hideRefreshIndicator(indicator) {
        indicator.style.transform = 'translateY(-100px)';
        indicator.style.opacity = '0';
        indicator.classList.remove('ready', 'refreshing');
        
        setTimeout(() => {
            indicator.style.transform = 'translateY(-100px)';
        }, 300);
    }

    setupHapticFeedback() {
        // Check if haptic feedback is supported
        this.hapticSupported = 'vibrate' in navigator;
    }

    triggerHaptic(intensity = 'light') {
        if (!this.hapticSupported) return;
        
        const patterns = {
            light: [10],
            medium: [20],
            heavy: [30],
            success: [10, 50, 10],
            error: [100, 50, 100]
        };
        
        const pattern = patterns[intensity] || patterns.light;
        navigator.vibrate(pattern);
    }

    preventDefaults() {
        // Prevent zoom on double tap for specific elements
        document.addEventListener('touchend', (event) => {
            const target = event.target;
            if (target.closest('.no-zoom')) {
                event.preventDefault();
            }
        }, { passive: false });

        // Prevent context menu on long press for specific elements
        document.addEventListener('contextmenu', (event) => {
            if (event.target.closest('.no-context-menu')) {
                event.preventDefault();
            }
        });
    }

    // Utility methods
    isAtLeftEdge() {
        return window.scrollX === 0;
    }

    showSwipeAction(element, message, type = 'info') {
        const indicator = document.createElement('div');
        indicator.className = `swipe-indicator ${type}`;
        indicator.textContent = message;
        
        element.appendChild(indicator);
        
        setTimeout(() => {
            indicator.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            indicator.classList.remove('show');
            setTimeout(() => {
                indicator.remove();
            }, 300);
        }, 2000);
    }

    showQuickActions(card) {
        const actions = document.createElement('div');
        actions.className = 'quick-actions';
        actions.innerHTML = `
            <button class="quick-action" onclick="this.closest('.quick-actions').remove()">
                <i data-feather="star"></i>
                <span>Watchlist</span>
            </button>
            <button class="quick-action" onclick="this.closest('.quick-actions').remove()">
                <i data-feather="trending-up"></i>
                <span>Predict</span>
            </button>
            <button class="quick-action" onclick="this.closest('.quick-actions').remove()">
                <i data-feather="bell"></i>
                <span>Alert</span>
            </button>
        `;
        
        card.appendChild(actions);
        
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (actions.parentNode) {
                actions.remove();
            }
        }, 5000);
    }

    showDeleteAction(item) {
        item.classList.add('swipe-delete');
        this.triggerHaptic('medium');
        
        setTimeout(() => {
            if (confirm('Delete this item?')) {
                item.remove();
                this.triggerHaptic('success');
            } else {
                item.classList.remove('swipe-delete');
            }
        }, 100);
    }

    showEditAction(item) {
        item.classList.add('swipe-edit');
        this.triggerHaptic('light');
        
        // Trigger edit functionality
        const editBtn = item.querySelector('.edit-btn, .edit-holding, .edit-alert');
        if (editBtn) {
            editBtn.click();
        }
        
        setTimeout(() => {
            item.classList.remove('swipe-edit');
        }, 300);
    }

    changeChartPeriod(container, direction) {
        const periodSelector = container.querySelector('.period-selector');
        if (periodSelector) {
            const options = periodSelector.querySelectorAll('option');
            const currentIndex = periodSelector.selectedIndex;
            
            let newIndex;
            if (direction === 'left') {
                newIndex = Math.min(currentIndex + 1, options.length - 1);
            } else {
                newIndex = Math.max(currentIndex - 1, 0);
            }
            
            if (newIndex !== currentIndex) {
                periodSelector.selectedIndex = newIndex;
                periodSelector.dispatchEvent(new Event('change'));
                this.triggerHaptic('light');
            }
        }
    }

    toggleExpansion(element) {
        element.classList.toggle('expanded');
        this.triggerHaptic('light');
    }

    showMetricDetails(card) {
        const details = card.querySelector('.metric-details');
        if (details) {
            details.classList.toggle('show');
        }
    }

    quickPrediction(card) {
        const symbol = card.dataset.symbol;
        if (symbol && window.app) {
            window.app.handleStockSearch(symbol);
            this.triggerHaptic('medium');
        }
    }

    toggleChartZoom(chart) {
        chart.classList.toggle('zoomed');
        this.triggerHaptic('medium');
    }

    executeLongPressAction(action, target) {
        switch (action) {
            case 'context-menu':
                this.showContextMenu(target);
                break;
            case 'quick-actions':
                this.showQuickActions(target);
                break;
            case 'delete':
                this.showDeleteAction(target);
                break;
            default:
                console.log('Unknown long press action:', action);
        }
    }

    showContextMenu(target) {
        const menu = document.createElement('div');
        menu.className = 'context-menu';
        menu.innerHTML = `
            <div class="context-menu-item" onclick="this.closest('.context-menu').remove()">
                <i data-feather="copy"></i>
                <span>Copy</span>
            </div>
            <div class="context-menu-item" onclick="this.closest('.context-menu').remove()">
                <i data-feather="share"></i>
                <span>Share</span>
            </div>
            <div class="context-menu-item" onclick="this.closest('.context-menu').remove()">
                <i data-feather="bookmark"></i>
                <span>Save</span>
            </div>
        `;
        
        document.body.appendChild(menu);
        
        // Position menu near target
        const rect = target.getBoundingClientRect();
        menu.style.left = rect.left + 'px';
        menu.style.top = (rect.bottom + 10) + 'px';
        
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
        
        // Auto-hide on outside click
        setTimeout(() => {
            document.addEventListener('click', function hideMenu() {
                menu.remove();
                document.removeEventListener('click', hideMenu);
            });
        }, 100);
    }

    zoomIn(target) {
        target.classList.add('zoom-in');
        this.triggerHaptic('light');
        
        setTimeout(() => {
            target.classList.remove('zoom-in');
        }, 300);
    }

    zoomOut(target) {
        target.classList.add('zoom-out');
        this.triggerHaptic('light');
        
        setTimeout(() => {
            target.classList.remove('zoom-out');
        }, 300);
    }

    // Public API
    registerGesture(name, callback) {
        this.gestures.set(name, callback);
    }

    unregisterGesture(name) {
        this.gestures.delete(name);
    }

    enable() {
        this.isEnabled = true;
    }

    disable() {
        this.isEnabled = false;
    }

    destroy() {
        // Remove all event listeners
        // In a real implementation, we'd need to store references to remove them
        console.log('MobileGestures: Destroyed');
    }
}

// Auto-initialize if on mobile device
if (typeof window !== 'undefined') {
    window.MobileGestures = MobileGestures;
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobileGestures;
}
