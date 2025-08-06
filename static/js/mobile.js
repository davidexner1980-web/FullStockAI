// FullStock AI vNext Ultimate - Mobile-Specific JavaScript
// Enhanced mobile trading experience with PWA features

class MobileManager {
  constructor() {
    this.isStandalone = window.matchMedia('(display-mode: standalone)').matches;
    this.isInstalled = this.isStandalone || window.navigator.standalone;
    this.installPrompt = null;
    this.touchStartX = 0;
    this.touchStartY = 0;
    this.isScrolling = false;
    this.keyboardHeight = 0;
    
    this.init();
  }
  
  init() {
    if (this.isMobile()) {
      this.setupPWAFeatures();
      this.setupTouchOptimization();
      this.setupKeyboardHandling();
      this.setupOrientationHandling();
      this.setupInstallPrompt();
      this.setupOfflineHandling();
      this.setupMobileNavigation();
      this.setupPullToRefresh();
      this.setupSwipeGestures();
      this.setupHapticFeedback();
      this.setupMobileCharts();
      this.setupQuickActions();
    }
  }
  
  isMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
           window.innerWidth <= 768;
  }
  
  isIOS() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent);
  }
  
  isAndroid() {
    return /Android/.test(navigator.userAgent);
  }
  
  setupPWAFeatures() {
    // Handle beforeinstallprompt event
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      this.installPrompt = e;
      this.showInstallBanner();
    });
    
    // Handle app installed event
    window.addEventListener('appinstalled', () => {
      this.hideInstallBanner();
      this.trackEvent('pwa_installed');
      app.showSuccess('FullStock AI installed successfully!');
    });
    
    // Check if running as PWA
    if (this.isStandalone) {
      document.body.classList.add('pwa-mode');
      this.hideBrowserUI();
    }
    
    // Add to home screen guidance for iOS
    if (this.isIOS() && !this.isInstalled) {
      this.showIOSInstallInstructions();
    }
  }
  
  showInstallBanner() {
    if (document.getElementById('installBanner')) return;
    
    const banner = document.createElement('div');
    banner.id = 'installBanner';
    banner.className = 'install-banner slide-in-down';
    banner.innerHTML = `
      <div class="install-banner-content">
        <div class="install-banner-icon">
          <i class="fas fa-mobile-alt"></i>
        </div>
        <div class="install-banner-text">
          <div class="install-banner-title">Install FullStock AI</div>
          <div class="install-banner-subtitle">Get the full mobile experience</div>
        </div>
        <div class="install-banner-actions">
          <button class="btn btn-primary btn-sm" onclick="mobileManager.installPWA()">
            Install
          </button>
          <button class="btn btn-secondary btn-sm" onclick="mobileManager.dismissInstallBanner()">
            Later
          </button>
        </div>
      </div>
    `;
    
    document.body.appendChild(banner);
    
    // Auto-hide after 10 seconds
    setTimeout(() => {
      if (document.getElementById('installBanner')) {
        this.dismissInstallBanner();
      }
    }, 10000);
  }
  
  async installPWA() {
    if (!this.installPrompt) return;
    
    const result = await this.installPrompt.prompt();
    
    if (result.outcome === 'accepted') {
      this.trackEvent('pwa_install_accepted');
    } else {
      this.trackEvent('pwa_install_dismissed');
    }
    
    this.installPrompt = null;
    this.hideInstallBanner();
  }
  
  dismissInstallBanner() {
    const banner = document.getElementById('installBanner');
    if (banner) {
      banner.classList.add('slide-out-up');
      setTimeout(() => banner.remove(), 300);
    }
    
    // Don't show again for 7 days
    localStorage.setItem('installBannerDismissed', Date.now() + (7 * 24 * 60 * 60 * 1000));
  }
  
  hideInstallBanner() {
    const banner = document.getElementById('installBanner');
    if (banner) {
      banner.remove();
    }
  }
  
  showIOSInstallInstructions() {
    const dismissed = localStorage.getItem('iosInstallDismissed');
    if (dismissed && Date.now() < parseInt(dismissed)) return;
    
    const modal = document.createElement('div');
    modal.className = 'ios-install-modal';
    modal.innerHTML = `
      <div class="ios-install-overlay" onclick="this.parentElement.remove()"></div>
      <div class="ios-install-content">
        <div class="ios-install-header">
          <h3>Add to Home Screen</h3>
          <button class="btn-close" onclick="this.closest('.ios-install-modal').remove()">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="ios-install-body">
          <p>Install FullStock AI for the best mobile experience:</p>
          <div class="ios-install-steps">
            <div class="ios-install-step">
              <i class="fas fa-share"></i>
              <span>1. Tap the Share button</span>
            </div>
            <div class="ios-install-step">
              <i class="fas fa-plus-square"></i>
              <span>2. Select "Add to Home Screen"</span>
            </div>
            <div class="ios-install-step">
              <i class="fas fa-check"></i>
              <span>3. Tap "Add"</span>
            </div>
          </div>
        </div>
        <div class="ios-install-footer">
          <button class="btn btn-secondary" onclick="mobileManager.dismissIOSInstructions()">
            Don't show again
          </button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
  }
  
  dismissIOSInstructions() {
    const modal = document.querySelector('.ios-install-modal');
    if (modal) {
      modal.remove();
    }
    
    // Don't show again for 30 days
    localStorage.setItem('iosInstallDismissed', Date.now() + (30 * 24 * 60 * 60 * 1000));
  }
  
  setupTouchOptimization() {
    // Optimize touch targets
    this.optimizeTouchTargets();
    
    // Prevent zoom on input focus for iOS
    if (this.isIOS()) {
      this.preventInputZoom();
    }
    
    // Add touch feedback
    this.addTouchFeedback();
    
    // Optimize scrolling
    this.optimizeScrolling();
  }
  
  optimizeTouchTargets() {
    const minTouchSize = 44; // 44px minimum for accessibility
    
    const touchElements = document.querySelectorAll('button, .btn, input, select, textarea, a');
    touchElements.forEach(element => {
      const rect = element.getBoundingClientRect();
      if (rect.width < minTouchSize || rect.height < minTouchSize) {
        element.style.minWidth = `${minTouchSize}px`;
        element.style.minHeight = `${minTouchSize}px`;
        element.classList.add('touch-optimized');
      }
    });
  }
  
  preventInputZoom() {
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
      if (input.type !== 'file') {
        input.style.fontSize = '16px'; // Prevents zoom on iOS
      }
    });
  }
  
  addTouchFeedback() {
    document.addEventListener('touchstart', (e) => {
      const target = e.target.closest('.btn, button, .touchable');
      if (target) {
        target.classList.add('touching');
        this.triggerHaptic('light');
      }
    });
    
    document.addEventListener('touchend', (e) => {
      const target = e.target.closest('.btn, button, .touchable');
      if (target) {
        setTimeout(() => {
          target.classList.remove('touching');
        }, 100);
      }
    });
  }
  
  optimizeScrolling() {
    // Enable momentum scrolling
    document.body.style.webkitOverflowScrolling = 'touch';
    
    // Prevent overscroll on iOS
    if (this.isIOS()) {
      document.addEventListener('touchmove', (e) => {
        if (e.scale !== 1) {
          e.preventDefault();
        }
      }, { passive: false });
    }
  }
  
  setupKeyboardHandling() {
    let initialViewportHeight = window.innerHeight;
    
    // Handle virtual keyboard
    window.addEventListener('resize', () => {
      const currentHeight = window.innerHeight;
      const heightDifference = initialViewportHeight - currentHeight;
      
      if (heightDifference > 150) { // Keyboard likely open
        this.keyboardHeight = heightDifference;
        document.body.classList.add('keyboard-open');
        this.adjustForKeyboard(true);
      } else {
        this.keyboardHeight = 0;
        document.body.classList.remove('keyboard-open');
        this.adjustForKeyboard(false);
      }
    });
    
    // Focus handling
    const inputs = document.querySelectorAll('input, textarea');
    inputs.forEach(input => {
      input.addEventListener('focus', () => {
        setTimeout(() => {
          this.scrollInputIntoView(input);
        }, 300);
      });
    });
  }
  
  adjustForKeyboard(isOpen) {
    const fixedElements = document.querySelectorAll('.floating-panel, .mobile-nav, .notification-container');
    
    fixedElements.forEach(element => {
      if (isOpen) {
        element.style.bottom = `${this.keyboardHeight}px`;
      } else {
        element.style.bottom = '';
      }
    });
  }
  
  scrollInputIntoView(input) {
    const rect = input.getBoundingClientRect();
    const availableHeight = window.innerHeight - this.keyboardHeight;
    
    if (rect.bottom > availableHeight) {
      const scrollAmount = rect.bottom - availableHeight + 20;
      window.scrollBy(0, scrollAmount);
    }
  }
  
  setupOrientationHandling() {
    window.addEventListener('orientationchange', () => {
      setTimeout(() => {
        this.handleOrientationChange();
      }, 500);
    });
    
    // Handle initial orientation
    this.handleOrientationChange();
  }
  
  handleOrientationChange() {
    const orientation = screen.orientation?.type || 
                      (window.innerHeight > window.innerWidth ? 'portrait' : 'landscape');
    
    document.body.classList.remove('portrait', 'landscape');
    document.body.classList.add(orientation.includes('portrait') ? 'portrait' : 'landscape');
    
    // Adjust chart heights
    if (app.chart) {
      setTimeout(() => {
        app.chart.resize();
      }, 100);
    }
    
    // Update viewport height
    this.setViewportHeight();
  }
  
  setViewportHeight() {
    const vh = window.innerHeight * 0.01;
    document.documentElement.style.setProperty('--vh', `${vh}px`);
  }
  
  setupInstallPrompt() {
    // Already handled in setupPWAFeatures
  }
  
  setupOfflineHandling() {
    window.addEventListener('online', () => {
      this.handleOnlineStatus(true);
    });
    
    window.addEventListener('offline', () => {
      this.handleOnlineStatus(false);
    });
    
    // Check initial status
    this.handleOnlineStatus(navigator.onLine);
  }
  
  handleOnlineStatus(isOnline) {
    const statusIndicator = this.getOrCreateStatusIndicator();
    
    statusIndicator.className = `connection-status ${isOnline ? 'online' : 'offline'}`;
    statusIndicator.textContent = isOnline ? 'Back online' : 'Offline mode';
    statusIndicator.style.display = 'block';
    
    if (isOnline) {
      setTimeout(() => {
        statusIndicator.style.display = 'none';
      }, 3000);
      
      // Sync offline data
      this.syncOfflineData();
    }
  }
  
  getOrCreateStatusIndicator() {
    let indicator = document.getElementById('connectionStatus');
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.id = 'connectionStatus';
      indicator.className = 'connection-status';
      document.body.appendChild(indicator);
    }
    return indicator;
  }
  
  setupMobileNavigation() {
    this.setupBottomNavigation();
    this.setupSideMenu();
    this.setupTabNavigation();
  }
  
  setupBottomNavigation() {
    const bottomNav = document.createElement('div');
    bottomNav.className = 'bottom-navigation';
    bottomNav.innerHTML = `
      <div class="bottom-nav-item active" data-page="dashboard">
        <i class="fas fa-chart-line"></i>
        <span>Analysis</span>
      </div>
      <div class="bottom-nav-item" data-page="crypto">
        <i class="fab fa-bitcoin"></i>
        <span>Crypto</span>
      </div>
      <div class="bottom-nav-item" data-page="portfolio">
        <i class="fas fa-briefcase"></i>
        <span>Portfolio</span>
      </div>
      <div class="bottom-nav-item" data-page="oracle">
        <i class="fas fa-crystal-ball"></i>
        <span>Oracle</span>
      </div>
      <div class="bottom-nav-item" data-page="settings">
        <i class="fas fa-cog"></i>
        <span>Settings</span>
      </div>
    `;
    
    document.body.appendChild(bottomNav);
    
    // Handle navigation
    bottomNav.addEventListener('click', (e) => {
      const navItem = e.target.closest('.bottom-nav-item');
      if (navItem) {
        this.navigateToPage(navItem.dataset.page);
        this.setActiveNavItem(navItem);
      }
    });
  }
  
  setupSideMenu() {
    // Side menu is already handled in the main app
    // This is for additional mobile optimizations
    
    const sideMenu = document.getElementById('mobileNav');
    if (sideMenu) {
      // Add swipe to close
      this.addSwipeToClose(sideMenu);
    }
  }
  
  addSwipeToClose(element) {
    let startX = 0;
    let currentX = 0;
    
    element.addEventListener('touchstart', (e) => {
      startX = e.touches[0].clientX;
    });
    
    element.addEventListener('touchmove', (e) => {
      currentX = e.touches[0].clientX;
      const diff = startX - currentX;
      
      if (diff > 0) { // Swiping left
        element.style.transform = `translateX(-${diff}px)`;
      }
    });
    
    element.addEventListener('touchend', () => {
      const diff = startX - currentX;
      
      if (diff > 100) { // Swipe threshold
        app.closeMobileMenu();
      } else {
        element.style.transform = '';
      }
      
      startX = 0;
      currentX = 0;
    });
  }
  
  setupTabNavigation() {
    const tabs = document.querySelectorAll('.tab-navigation');
    tabs.forEach(tabContainer => {
      this.makeTabsSwipeable(tabContainer);
    });
  }
  
  makeTabsSwipeable(tabContainer) {
    let startX = 0;
    let currentTab = 0;
    const tabs = tabContainer.querySelectorAll('.tab-content');
    
    tabContainer.addEventListener('touchstart', (e) => {
      startX = e.touches[0].clientX;
    });
    
    tabContainer.addEventListener('touchend', (e) => {
      const endX = e.changedTouches[0].clientX;
      const diff = startX - endX;
      
      if (Math.abs(diff) > 50) { // Swipe threshold
        if (diff > 0 && currentTab < tabs.length - 1) {
          // Swipe left - next tab
          this.switchTab(tabContainer, currentTab + 1);
        } else if (diff < 0 && currentTab > 0) {
          // Swipe right - previous tab
          this.switchTab(tabContainer, currentTab - 1);
        }
      }
    });
  }
  
  switchTab(tabContainer, index) {
    const tabs = tabContainer.querySelectorAll('.tab-content');
    const navItems = tabContainer.querySelectorAll('.tab-nav-item');
    
    tabs.forEach((tab, i) => {
      tab.classList.toggle('active', i === index);
    });
    
    navItems.forEach((item, i) => {
      item.classList.toggle('active', i === index);
    });
  }
  
  setupPullToRefresh() {
    let startY = 0;
    let currentY = 0;
    let pullDistance = 0;
    let isPulling = false;
    let refreshThreshold = 70;
    
    const refreshIndicator = this.createPullToRefreshIndicator();
    
    document.addEventListener('touchstart', (e) => {
      if (window.scrollY === 0 && !this.isScrolling) {
        startY = e.touches[0].clientY;
        isPulling = true;
      }
    }, { passive: true });
    
    document.addEventListener('touchmove', (e) => {
      if (!isPulling) return;
      
      currentY = e.touches[0].clientY;
      pullDistance = Math.max(0, currentY - startY);
      
      if (pullDistance > 0 && window.scrollY === 0) {
        e.preventDefault();
        
        const progress = Math.min(pullDistance / refreshThreshold, 1);
        this.updateRefreshIndicator(refreshIndicator, progress, pullDistance >= refreshThreshold);
        
        // Add resistance effect
        const resistance = pullDistance > refreshThreshold ? 0.5 : 1;
        document.body.style.transform = `translateY(${pullDistance * resistance}px)`;
      }
    }, { passive: false });
    
    document.addEventListener('touchend', () => {
      if (isPulling) {
        document.body.style.transform = '';
        
        if (pullDistance >= refreshThreshold) {
          this.triggerRefresh(refreshIndicator);
        } else {
          this.hideRefreshIndicator(refreshIndicator);
        }
        
        isPulling = false;
        pullDistance = 0;
      }
    }, { passive: true });
  }
  
  createPullToRefreshIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'pull-refresh-indicator';
    indicator.innerHTML = `
      <div class="pull-refresh-content">
        <i class="fas fa-arrow-down pull-refresh-icon"></i>
        <span class="pull-refresh-text">Pull to refresh</span>
      </div>
    `;
    
    document.body.insertBefore(indicator, document.body.firstChild);
    return indicator;
  }
  
  updateRefreshIndicator(indicator, progress, canRefresh) {
    const icon = indicator.querySelector('.pull-refresh-icon');
    const text = indicator.querySelector('.pull-refresh-text');
    
    indicator.style.opacity = progress;
    indicator.style.transform = `scale(${0.8 + (progress * 0.2)})`;
    
    if (canRefresh) {
      icon.className = 'fas fa-sync-alt pull-refresh-icon';
      text.textContent = 'Release to refresh';
      this.triggerHaptic('medium');
    } else {
      icon.className = 'fas fa-arrow-down pull-refresh-icon';
      text.textContent = 'Pull to refresh';
    }
  }
  
  async triggerRefresh(indicator) {
    const icon = indicator.querySelector('.pull-refresh-icon');
    const text = indicator.querySelector('.pull-refresh-text');
    
    icon.className = 'fas fa-sync-alt fa-spin pull-refresh-icon';
    text.textContent = 'Refreshing...';
    indicator.style.opacity = '1';
    
    try {
      await app.refreshCurrentAnalysis();
      this.triggerHaptic('success');
    } catch (error) {
      this.triggerHaptic('error');
    }
    
    setTimeout(() => {
      this.hideRefreshIndicator(indicator);
    }, 1000);
  }
  
  hideRefreshIndicator(indicator) {
    indicator.style.opacity = '0';
    indicator.style.transform = 'scale(0.8)';
  }
  
  setupSwipeGestures() {
    let touchStartX = 0;
    let touchStartY = 0;
    let touchEndX = 0;
    let touchEndY = 0;
    
    document.addEventListener('touchstart', (e) => {
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
    }, { passive: true });
    
    document.addEventListener('touchend', (e) => {
      touchEndX = e.changedTouches[0].clientX;
      touchEndY = e.changedTouches[0].clientY;
      
      this.handleSwipeGesture(touchStartX, touchStartY, touchEndX, touchEndY);
    }, { passive: true });
  }
  
  handleSwipeGesture(startX, startY, endX, endY) {
    const deltaX = endX - startX;
    const deltaY = endY - startY;
    const minSwipeDistance = 50;
    
    // Determine swipe direction
    if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > minSwipeDistance) {
      if (deltaX > 0) {
        this.handleSwipeRight();
      } else {
        this.handleSwipeLeft();
      }
    } else if (Math.abs(deltaY) > minSwipeDistance) {
      if (deltaY > 0) {
        this.handleSwipeDown();
      } else {
        this.handleSwipeUp();
      }
    }
  }
  
  handleSwipeLeft() {
    // Navigate to next section or close panels
    const panels = document.querySelectorAll('.floating-panel.active');
    if (panels.length > 0) {
      panels.forEach(panel => panel.classList.remove('active'));
    }
  }
  
  handleSwipeRight() {
    // Open navigation menu
    if (!document.getElementById('mobileNav').classList.contains('active')) {
      app.toggleMobileMenu();
    }
  }
  
  handleSwipeDown() {
    // Show notifications or additional info
    this.showQuickInfo();
  }
  
  handleSwipeUp() {
    // Hide floating elements or show full-screen mode
    this.toggleFullScreenMode();
  }
  
  setupHapticFeedback() {
    this.hapticSupported = 'vibrate' in navigator;
    
    if (this.hapticSupported) {
      // Add haptic feedback to various interactions
      document.addEventListener('click', (e) => {
        if (e.target.matches('.btn-primary, .btn-oracle')) {
          this.triggerHaptic('medium');
        } else if (e.target.matches('.btn, button')) {
          this.triggerHaptic('light');
        }
      });
    }
  }
  
  triggerHaptic(type = 'light', customPattern = null) {
    if (!this.hapticSupported) return;
    
    const patterns = {
      light: [10],
      medium: [20],
      heavy: [40],
      success: [10, 50, 10],
      error: [100, 50, 100],
      notification: [50, 20, 50, 20, 50]
    };
    
    const pattern = customPattern || patterns[type] || patterns.light;
    navigator.vibrate(pattern);
  }
  
  setupMobileCharts() {
    // Optimize Chart.js for mobile
    if (typeof Chart !== 'undefined') {
      Chart.defaults.elements.point.radius = 3;
      Chart.defaults.elements.point.hoverRadius = 6;
      Chart.defaults.elements.line.borderWidth = 2;
      Chart.defaults.plugins.tooltip.bodySpacing = 8;
      Chart.defaults.plugins.tooltip.padding = 12;
      
      // Mobile-specific chart options
      this.mobileChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false // Hide legend on mobile to save space
          },
          tooltip: {
            mode: 'nearest',
            intersect: false,
            position: 'nearest'
          }
        },
        scales: {
          x: {
            display: true,
            ticks: {
              maxTicksLimit: 6 // Limit x-axis labels
            }
          },
          y: {
            display: true,
            ticks: {
              maxTicksLimit: 5 // Limit y-axis labels
            }
          }
        },
        interaction: {
          intersect: false,
          mode: 'index'
        }
      };
    }
  }
  
  setupQuickActions() {
    this.createFloatingActionButton();
    this.setupVoiceSearch();
    this.setupQuickSearches();
  }
  
  createFloatingActionButton() {
    const fab = document.createElement('div');
    fab.className = 'floating-action-button';
    fab.innerHTML = `
      <button class="fab-main">
        <i class="fas fa-plus"></i>
      </button>
      <div class="fab-menu">
        <button class="fab-action" data-action="voice-search">
          <i class="fas fa-microphone"></i>
        </button>
        <button class="fab-action" data-action="quick-analyze">
          <i class="fas fa-bolt"></i>
        </button>
        <button class="fab-action" data-action="add-alert">
          <i class="fas fa-bell"></i>
        </button>
        <button class="fab-action" data-action="share">
          <i class="fas fa-share"></i>
        </button>
      </div>
    `;
    
    document.body.appendChild(fab);
    
    // FAB interactions
    const mainButton = fab.querySelector('.fab-main');
    const menu = fab.querySelector('.fab-menu');
    
    mainButton.addEventListener('click', () => {
      fab.classList.toggle('active');
      this.triggerHaptic('medium');
    });
    
    // Handle FAB actions
    fab.addEventListener('click', (e) => {
      const action = e.target.closest('.fab-action');
      if (action) {
        this.handleFabAction(action.dataset.action);
        fab.classList.remove('active');
      }
    });
  }
  
  handleFabAction(action) {
    switch (action) {
      case 'voice-search':
        this.startVoiceSearch();
        break;
      case 'quick-analyze':
        this.showQuickAnalyze();
        break;
      case 'add-alert':
        this.showAddAlert();
        break;
      case 'share':
        this.shareCurrentAnalysis();
        break;
    }
  }
  
  setupVoiceSearch() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      this.recognition = new SpeechRecognition();
      
      this.recognition.continuous = false;
      this.recognition.interimResults = false;
      this.recognition.lang = 'en-US';
      
      this.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript.trim().toUpperCase();
        this.handleVoiceCommand(transcript);
      };
      
      this.recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        app.showError('Voice search failed. Please try again.');
      };
    }
  }
  
  startVoiceSearch() {
    if (!this.recognition) {
      app.showError('Voice search not supported on this device');
      return;
    }
    
    this.showVoiceSearchUI();
    
    try {
      this.recognition.start();
      this.triggerHaptic('medium');
    } catch (error) {
      app.showError('Could not start voice recognition');
    }
  }
  
  showVoiceSearchUI() {
    const modal = document.createElement('div');
    modal.className = 'voice-search-modal';
    modal.innerHTML = `
      <div class="voice-search-overlay" onclick="this.parentElement.remove()"></div>
      <div class="voice-search-content">
        <div class="voice-search-animation">
          <div class="voice-wave"></div>
          <div class="voice-wave"></div>
          <div class="voice-wave"></div>
        </div>
        <h3>Listening...</h3>
        <p>Say a stock ticker symbol</p>
        <button class="btn btn-secondary" onclick="mobileManager.stopVoiceSearch()">
          Cancel
        </button>
      </div>
    `;
    
    document.body.appendChild(modal);
  }
  
  stopVoiceSearch() {
    if (this.recognition) {
      this.recognition.stop();
    }
    
    const modal = document.querySelector('.voice-search-modal');
    if (modal) {
      modal.remove();
    }
  }
  
  handleVoiceCommand(command) {
    this.stopVoiceSearch();
    
    // Check if it's a valid ticker format
    if (/^[A-Z]{1,5}$/.test(command)) {
      app.analyzeTicker(command);
      app.showSuccess(`Analyzing ${command}...`);
    } else {
      app.showError(`"${command}" doesn't look like a valid ticker symbol`);
    }
  }
  
  setupQuickSearches() {
    const quickSearches = ['AAPL', 'TSLA', 'GOOGL', 'MSFT', 'AMZN', 'META', 'NVDA', 'BTC-USD'];
    
    const container = document.getElementById('quickSearches');
    if (container) {
      container.innerHTML = quickSearches.map(ticker => `
        <button class="btn btn-outline btn-sm quick-search-btn" onclick="app.analyzeTicker('${ticker}')">
          ${ticker}
        </button>
      `).join('');
    }
  }
  
  // Navigation helpers
  navigateToPage(page) {
    const routes = {
      'dashboard': '/',
      'crypto': '/crypto',
      'portfolio': '/portfolio',
      'oracle': '/?oracle=true',
      'settings': '#settings'
    };
    
    const route = routes[page];
    if (route) {
      if (route.startsWith('#')) {
        this.showSettingsModal();
      } else {
        window.location.href = route;
      }
    }
  }
  
  setActiveNavItem(activeItem) {
    const navItems = document.querySelectorAll('.bottom-nav-item');
    navItems.forEach(item => {
      item.classList.remove('active');
    });
    activeItem.classList.add('active');
  }
  
  showSettingsModal() {
    const modal = document.createElement('div');
    modal.className = 'settings-modal';
    modal.innerHTML = `
      <div class="settings-overlay" onclick="this.parentElement.remove()"></div>
      <div class="settings-content">
        <div class="settings-header">
          <h3>Settings</h3>
          <button class="btn-close" onclick="this.closest('.settings-modal').remove()">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="settings-body">
          <div class="settings-group">
            <label class="settings-label">
              <input type="checkbox" id="hapticFeedback" ${this.hapticSupported ? 'checked' : ''}>
              <span>Haptic Feedback</span>
            </label>
            <label class="settings-label">
              <input type="checkbox" id="voiceSearch" ${this.recognition ? 'checked' : ''}>
              <span>Voice Search</span>
            </label>
            <label class="settings-label">
              <input type="checkbox" id="pushNotifications">
              <span>Push Notifications</span>
            </label>
          </div>
          <div class="settings-group">
            <button class="btn btn-primary btn-block" onclick="mobileManager.clearCache()">
              Clear Cache
            </button>
            <button class="btn btn-secondary btn-block" onclick="mobileManager.exportData()">
              Export Data
            </button>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
  }
  
  // Utility functions
  showQuickInfo() {
    if (app.currentTicker) {
      const info = `Current: ${app.currentTicker} | Online: ${navigator.onLine ? 'Yes' : 'No'}`;
      app.showNotification(info, 'info');
    }
  }
  
  toggleFullScreenMode() {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      document.documentElement.requestFullscreen();
    }
  }
  
  hideBrowserUI() {
    // Hide browser UI elements in PWA mode
    const metaTheme = document.querySelector('meta[name="theme-color"]');
    if (metaTheme) {
      metaTheme.setAttribute('content', '#0d1117');
    }
  }
  
  syncOfflineData() {
    // Sync any offline data when connection is restored
    console.log('Syncing offline data...');
  }
  
  clearCache() {
    if ('caches' in window) {
      caches.keys().then(names => {
        names.forEach(name => {
          caches.delete(name);
        });
      });
    }
    
    localStorage.clear();
    app.showSuccess('Cache cleared successfully');
  }
  
  exportData() {
    const data = {
      watchlist: app.state.watchlist,
      searchHistory: JSON.parse(localStorage.getItem('searchHistory') || '[]'),
      preferences: JSON.parse(localStorage.getItem('userPreferences') || '{}'),
      timestamp: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `fullstock-data-${Date.now()}.json`;
    a.click();
    
    URL.revokeObjectURL(url);
  }
  
  trackEvent(event, data = {}) {
    // Analytics tracking
    console.log('Event:', event, data);
  }
}

// Initialize mobile manager
document.addEventListener('DOMContentLoaded', () => {
  window.mobileManager = new MobileManager();
});

// Add CSS for mobile-specific components
const mobileStyles = `
.install-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: linear-gradient(45deg, #3b82f6, #1d4ed8);
  color: white;
  z-index: 1000;
  padding: 12px 16px;
}

.install-banner-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.install-banner-icon {
  font-size: 24px;
}

.install-banner-text {
  flex: 1;
}

.install-banner-title {
  font-weight: 600;
  font-size: 14px;
}

.install-banner-subtitle {
  font-size: 12px;
  opacity: 0.9;
}

.install-banner-actions {
  display: flex;
  gap: 8px;
}

.ios-install-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2000;
}

.ios-install-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
}

.ios-install-content {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--bg-secondary);
  border-radius: 16px 16px 0 0;
  padding: 24px;
  animation: slideInUp 0.3s ease-out;
}

.ios-install-steps {
  margin: 20px 0;
}

.ios-install-step {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  color: var(--text-secondary);
}

.bottom-navigation {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--bg-secondary);
  border-top: 1px solid var(--bg-tertiary);
  display: flex;
  padding: 8px 0;
  z-index: 100;
}

.bottom-nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 4px;
  color: var(--text-muted);
  font-size: 10px;
  cursor: pointer;
  transition: color 0.2s ease;
}

.bottom-nav-item.active {
  color: var(--brand-primary);
}

.bottom-nav-item i {
  font-size: 18px;
  margin-bottom: 4px;
}

.floating-action-button {
  position: fixed;
  bottom: 80px;
  right: 20px;
  z-index: 1000;
}

.fab-main {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(45deg, var(--brand-primary), var(--brand-secondary));
  color: white;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: transform 0.2s ease;
}

.fab-main:active {
  transform: scale(0.9);
}

.fab-menu {
  position: absolute;
  bottom: 70px;
  right: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease;
}

.floating-action-button.active .fab-menu {
  opacity: 1;
  visibility: visible;
}

.fab-action {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--bg-secondary);
  border: 1px solid var(--bg-tertiary);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.voice-search-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2000;
}

.voice-search-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
}

.voice-search-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: var(--bg-secondary);
  border-radius: 16px;
  padding: 32px;
  text-align: center;
  min-width: 280px;
}

.voice-search-animation {
  display: flex;
  justify-content: center;
  gap: 4px;
  margin-bottom: 16px;
}

.voice-wave {
  width: 4px;
  height: 20px;
  background: var(--brand-primary);
  border-radius: 2px;
  animation: voiceWave 1.5s ease-in-out infinite;
}

.voice-wave:nth-child(2) {
  animation-delay: 0.2s;
}

.voice-wave:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes voiceWave {
  0%, 100% { height: 20px; }
  50% { height: 40px; }
}

.pull-refresh-indicator {
  position: fixed;
  top: -60px;
  left: 0;
  right: 0;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  color: var(--text-muted);
  z-index: 999;
  opacity: 0;
  transform: scale(0.8);
  transition: all 0.2s ease;
}

.connection-status {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  z-index: 1001;
  display: none;
}

.connection-status.online {
  background: var(--success);
  color: white;
}

.connection-status.offline {
  background: var(--danger);
  color: white;
}

.touching {
  transform: scale(0.95);
  opacity: 0.8;
}

@media (max-width: 768px) {
  body {
    padding-bottom: 70px; /* Space for bottom navigation */
  }
  
  .keyboard-open {
    height: 100vh;
    overflow: hidden;
  }
  
  .pwa-mode .header {
    padding-top: env(safe-area-inset-top);
  }
  
  .pwa-mode .bottom-navigation {
    padding-bottom: env(safe-area-inset-bottom);
  }
}

.slide-in-down {
  animation: slideInDown 0.3s ease-out;
}

.slide-out-up {
  animation: slideOutUp 0.3s ease-out;
}

@keyframes slideInDown {
  from {
    transform: translateY(-100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes slideOutUp {
  from {
    transform: translateY(0);
    opacity: 1;
  }
  to {
    transform: translateY(-100%);
    opacity: 0;
  }
}

@keyframes slideInUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
`;

// Inject mobile styles
const styleSheet = document.createElement('style');
styleSheet.textContent = mobileStyles;
document.head.appendChild(styleSheet);
