// SENTINEL Fire Detection Command Center
const { invoke } = window.__TAURI__.core;

class SentinelCommandCenter {
    constructor() {
        this.currentView = 'command';
        this.alertData = [];
        this.systemStatus = {
            cameras: 3,
            activeAlerts: 0,
            uptime: 99.9,
            systemHealth: 'optimal'
        };
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.renderInterface();
        this.startRealTimeUpdates();
    }

    setupEventListeners() {
        // Use event delegation with immediate response for better UX
        document.addEventListener('click', (e) => {
            // Prevent double-clicks and ensure single execution
            if (e.detail > 1) return;
            
            // Find closest element with data attributes (for nested elements)
            const viewTarget = e.target.closest('[data-view]');
            const actionTarget = e.target.closest('[data-action]');
            
            if (viewTarget?.dataset.view) {
                e.preventDefault();
                this.switchView(viewTarget.dataset.view);
            }
            
            if (actionTarget?.dataset.action) {
                e.preventDefault();
                this.handleAction(actionTarget.dataset.action, actionTarget.dataset.id);
            }
        });
        
        // Add hover feedback for better responsiveness feel
        document.addEventListener('mouseover', (e) => {
            const button = e.target.closest('button[data-view], button[data-action]');
            if (button && !button.classList.contains('bg-fire-500')) {
                button.style.transform = 'translateY(-1px)';
            }
        });
        
        document.addEventListener('mouseout', (e) => {
            const button = e.target.closest('button[data-view], button[data-action]');
            if (button) {
                button.style.transform = '';
            }
        });
    }

    switchView(viewName) {
        document.querySelectorAll('[data-view]').forEach(item => {
            item.classList.remove('bg-fire-500', 'text-white');
            item.classList.add('text-gray-300', 'hover:text-white');
        });
        
        const activeTab = document.querySelector(`[data-view="${viewName}"]`);
        if (activeTab) {
            activeTab.classList.remove('text-gray-300', 'hover:text-white');
            activeTab.classList.add('bg-fire-500', 'text-white');
        }

        this.currentView = viewName;
        this.renderMainContent();
    }

    renderInterface() {
        document.getElementById('app').innerHTML = `
            <!-- Command Header -->
            <header class="h-16 bg-gradient-to-r from-command-900 via-command-800 to-safety-900 border-b border-fire-500/30 flex items-center justify-between px-6">
                <div class="flex items-center space-x-4">
                    <div class="w-8 h-8 fire-gradient rounded-lg flex items-center justify-center" style="animation: subtle-pulse 4s ease-in-out infinite">
                        <div class="w-4 h-4 bg-white rounded-sm"></div>
                    </div>
                    <div>
                        <h1 class="text-xl font-bold font-display text-white">SENTINEL</h1>
                        <p class="text-xs text-fire-300 font-command">FIRE COMMAND CENTER</p>
                    </div>
                </div>
                
                <div class="flex items-center space-x-6">
                    <div class="flex items-center space-x-2">
                        <div class="w-3 h-3 status-online rounded-full"></div>
                        <span class="text-sm font-command text-emerald-400">SYSTEM ONLINE</span>
                    </div>
                    <div class="text-right">
                        <div class="text-sm font-command text-white" id="current-time"></div>
                        <div class="text-xs text-gray-400">LOCAL TIME</div>
                    </div>
                </div>
            </header>

            <!-- Main Interface -->
            <div class="flex-1 flex overflow-hidden">
                <!-- Command Navigation -->
                <nav class="w-64 bg-command-800 border-r border-command-600 p-4 space-y-2">
                    <div class="mb-6">
                        <h2 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">OPERATIONS</h2>
                        <div class="space-y-1">
                            <button data-view="command" class="w-full flex items-center space-x-3 px-3 py-2 rounded-lg bg-fire-500 text-white text-sm font-medium">
                                <div class="w-4 h-4 bg-current rounded-sm"></div>
                                <span>Command Center</span>
                            </button>
                            <button data-view="surveillance" class="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-command-700 text-sm font-medium transition-colors hover-lift">
                                <div class="w-4 h-4 bg-current rounded-sm"></div>
                                <span>Surveillance Grid</span>
                            </button>
                            <button data-view="incidents" class="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-command-700 text-sm font-medium transition-colors hover-lift">
                                <div class="w-4 h-4 bg-current rounded-sm"></div>
                                <span>Incident Management</span>
                            </button>
                            <button data-view="analytics" class="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-command-700 text-sm font-medium transition-colors hover-lift">
                                <div class="w-4 h-4 bg-current rounded-sm"></div>
                                <span>Analytics Center</span>
                            </button>
                        </div>
                    </div>

                    <div class="mb-6">
                        <h2 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">CONFIGURATION</h2>
                        <div class="space-y-1">
                            <button data-view="settings" class="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-command-700 text-sm font-medium transition-colors hover-lift">
                                <div class="w-4 h-4 bg-current rounded-sm"></div>
                                <span>Detection Settings</span>
                            </button>
                            <button data-view="system" class="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-command-700 text-sm font-medium transition-colors hover-lift">
                                <div class="w-4 h-4 bg-current rounded-sm"></div>
                                <span>System Health</span>
                            </button>
                        </div>
                    </div>

                    <!-- Critical Status Panel -->
                    <div class="command-panel rounded-lg p-4 mt-8">
                        <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">SYSTEM STATUS</h3>
                        <div class="space-y-3">
                            <div class="flex justify-between items-center">
                                <span class="text-sm text-gray-300">Detection Engine</span>
                                <div class="flex items-center space-x-2">
                                    <div class="w-2 h-2 bg-emerald-500 rounded-full animate-slow-pulse"></div>
                                    <span class="text-xs font-command text-emerald-400">ACTIVE</span>
                                </div>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-sm text-gray-300">Camera Grid</span>
                                <div class="flex items-center space-x-2">
                                    <div class="w-2 h-2 bg-emerald-500 rounded-full animate-slow-pulse"></div>
                                    <span class="text-xs font-command text-emerald-400">3/3 ONLINE</span>
                                </div>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-sm text-gray-300">Alert System</span>
                                <div class="flex items-center space-x-2">
                                    <div class="w-2 h-2 bg-emerald-500 rounded-full animate-slow-pulse"></div>
                                    <span class="text-xs font-command text-emerald-400">READY</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </nav>

                <!-- Main Content Area -->
                <main class="flex-1 overflow-auto" id="main-content">
                    <!-- Content will be rendered here -->
                </main>
            </div>
        `;
        
        this.renderMainContent();
        this.updateClock();
        this.intervals.push(setInterval(() => this.updateClock(), 1000));
    }

    renderMainContent() {
        const content = document.getElementById('main-content');
        
        switch (this.currentView) {
            case 'command':
                content.innerHTML = this.renderCommandCenter();
                break;
            case 'surveillance':
                content.innerHTML = this.renderSurveillanceGrid();
                break;
            case 'incidents':
                content.innerHTML = this.renderIncidentManagement();
                break;
            case 'analytics':
                content.innerHTML = this.renderAnalyticsCenter();
                break;
            case 'settings':
                content.innerHTML = this.renderDetectionSettings();
                break;
            case 'system':
                content.innerHTML = this.renderSystemHealth();
                break;
            default:
                content.innerHTML = this.renderCommandCenter();
        }
    }

    renderCommandCenter() {
        return `
            <div class="p-6 space-y-6">
                <!-- Critical Metrics Row -->
                <div class="grid grid-cols-4 gap-6">
                    <div class="command-panel rounded-xl p-6">
                        <div class="flex items-center justify-between mb-2">
                            <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider">THREAT LEVEL</h3>
                            <div class="w-3 h-3 bg-emerald-500 rounded-full animate-slow-pulse"></div>
                        </div>
                        <div class="text-3xl font-bold font-command text-emerald-400 mb-1">LOW</div>
                        <div class="text-xs text-gray-500">No active threats detected</div>
                    </div>
                    
                    <div class="command-panel rounded-xl p-6">
                        <div class="flex items-center justify-between mb-2">
                            <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider">ACTIVE CAMERAS</h3>
                            <div class="w-3 h-3 bg-fire-500 rounded-full animate-slow-pulse"></div>
                        </div>
                        <div class="text-3xl font-bold font-command text-white mb-1" id="camera-count">3</div>
                        <div class="text-xs text-gray-500">All systems operational</div>
                    </div>
                    
                    <div class="command-panel rounded-xl p-6">
                        <div class="flex items-center justify-between mb-2">
                            <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider">ALERTS TODAY</h3>
                            <div class="w-3 h-3 bg-warning-500 rounded-full animate-slow-pulse"></div>
                        </div>
                        <div class="text-3xl font-bold font-command text-warning-400 mb-1" id="alert-count">0</div>
                        <div class="text-xs text-gray-500">Last 24 hours</div>
                    </div>
                    
                    <div class="command-panel rounded-xl p-6">
                        <div class="flex items-center justify-between mb-2">
                            <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider">SYSTEM UPTIME</h3>
                            <div class="w-3 h-3 bg-safety-500 rounded-full animate-slow-pulse"></div>
                        </div>
                        <div class="text-3xl font-bold font-command text-safety-400 mb-1">99.9%</div>
                        <div class="text-xs text-gray-500">Operational excellence</div>
                    </div>
                </div>

                <!-- Detection Thresholds Panel -->
                <div class="command-panel rounded-xl p-6">
                    <h3 class="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                        <div class="w-5 h-5 fire-gradient rounded"></div>
                        <span>DETECTION PARAMETERS</span>
                    </h3>
                    <div class="grid grid-cols-3 gap-6">
                        <div class="bg-command-700 rounded-lg p-4">
                            <div class="flex items-center justify-between mb-3">
                                <span class="text-sm font-semibold text-emergency-400">P1 - IMMEDIATE</span>
                                <span class="text-xl font-command text-white">95%</span>
                            </div>
                            <div class="w-full bg-command-600 rounded-full h-2">
                                <div class="bg-gradient-to-r from-emergency-600 to-emergency-400 h-2 rounded-full" style="width: 95%"></div>
                            </div>
                            <div class="text-xs text-gray-400 mt-2">Automatic dispatch</div>
                        </div>
                        
                        <div class="bg-command-700 rounded-lg p-4">
                            <div class="flex items-center justify-between mb-3">
                                <span class="text-sm font-semibold text-warning-400">P2 - REVIEW</span>
                                <span class="text-xl font-command text-white">85%</span>
                            </div>
                            <div class="w-full bg-command-600 rounded-full h-2">
                                <div class="bg-gradient-to-r from-warning-600 to-warning-400 h-2 rounded-full" style="width: 85%"></div>
                            </div>
                            <div class="text-xs text-gray-400 mt-2">Human verification</div>
                        </div>
                        
                        <div class="bg-command-700 rounded-lg p-4">
                            <div class="flex items-center justify-between mb-3">
                                <span class="text-sm font-semibold text-safety-400">P4 - LOG</span>
                                <span class="text-xl font-command text-white">70%</span>
                            </div>
                            <div class="w-full bg-command-600 rounded-full h-2">
                                <div class="bg-gradient-to-r from-safety-600 to-safety-400 h-2 rounded-full" style="width: 70%"></div>
                            </div>
                            <div class="text-xs text-gray-400 mt-2">Data collection</div>
                        </div>
                    </div>
                </div>

                <!-- Live Activity Feed -->
                <div class="command-panel rounded-xl p-6">
                    <h3 class="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                        <div class="w-5 h-5 bg-emerald-500 rounded animate-slow-pulse"></div>
                        <span>LIVE ACTIVITY FEED</span>
                    </h3>
                    <div class="space-y-3 max-h-80 overflow-auto" id="activity-feed">
                        <div class="text-center text-gray-500 py-8">
                            <div class="w-12 h-12 bg-command-700 rounded-full mx-auto mb-3 flex items-center justify-center">
                                <div class="w-6 h-6 bg-command-600 rounded"></div>
                            </div>
                            <p>Monitoring all camera feeds...</p>
                            <p class="text-sm">Alerts will appear here in real-time</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderSurveillanceGrid() {
        return `
            <div class="p-6">
                <div class="mb-6">
                    <h2 class="text-2xl font-bold text-white mb-2">SURVEILLANCE GRID</h2>
                    <p class="text-gray-400">Real-time monitoring of all camera feeds</p>
                </div>
                
                <div class="grid grid-cols-2 gap-6">
                    ${this.renderCameraFeed('CAM_001', 'OUTDOOR PERIMETER', 'online', 'No threats detected')}
                    ${this.renderCameraFeed('CAM_002', 'INDOOR FACILITY', 'online', 'Clear visibility')}
                    ${this.renderCameraFeed('CAM_003', 'SYNTHETIC FEED', 'online', 'Simulation active')}
                    ${this.renderCameraFeed('CAM_004', 'BACKUP UNIT', 'offline', 'Maintenance mode')}
                </div>
            </div>
        `;
    }

    renderCameraFeed(id, location, status, statusText) {
        const statusColor = status === 'online' ? 'emerald' : 'gray';
        return `
            <div class="command-panel rounded-xl overflow-hidden">
                <div class="bg-command-700 p-4 border-b border-command-600">
                    <div class="flex items-center justify-between">
                        <div>
                            <h3 class="font-semibold text-white font-command">${id}</h3>
                            <p class="text-sm text-gray-400">${location}</p>
                        </div>
                        <div class="flex items-center space-x-2">
                            <div class="w-2 h-2 bg-${statusColor}-500 rounded-full animate-slow-pulse"></div>
                            <span class="text-xs font-command text-${statusColor}-400 uppercase">${status}</span>
                        </div>
                    </div>
                </div>
                <div class="bg-black h-48 flex items-center justify-center relative">
                    <div class="text-center">
                        <div class="w-16 h-16 bg-command-700 rounded-lg mx-auto mb-3 flex items-center justify-center">
                            <div class="w-8 h-8 bg-command-600 rounded"></div>
                        </div>
                        <p class="text-gray-400 text-sm">${statusText}</p>
                    </div>
                    ${status === 'online' ? `
                        <div class="absolute top-2 right-2 bg-emerald-500 text-white text-xs px-2 py-1 rounded font-command">
                            LIVE
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    renderIncidentManagement() {
        return `
            <div class="p-6">
                <div class="mb-6">
                    <h2 class="text-2xl font-bold text-white mb-2">INCIDENT MANAGEMENT</h2>
                    <p class="text-gray-400">Active alerts and incident response</p>
                </div>
                
                <div class="command-panel rounded-xl p-6">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-semibold text-white">ACTIVE INCIDENTS</h3>
                        <button data-action="clear-alerts" class="bg-fire-500 hover:bg-fire-600 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors hover-lift">
                            ACKNOWLEDGE ALL
                        </button>
                    </div>
                    <div id="incidents-list" class="space-y-3">
                        <div class="text-center text-gray-500 py-12">
                            <div class="w-16 h-16 bg-emerald-500 rounded-full mx-auto mb-4 flex items-center justify-center">
                                <div class="w-8 h-8 bg-white rounded"></div>
                            </div>
                            <p class="text-lg font-semibold text-emerald-400">ALL CLEAR</p>
                            <p class="text-sm">No active incidents detected</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderAnalyticsCenter() {
        return `
            <div class="p-6">
                <div class="mb-6">
                    <h2 class="text-2xl font-bold text-white mb-2">ANALYTICS CENTER</h2>
                    <p class="text-gray-400">Performance metrics and insights</p>
                </div>
                
                <div class="grid grid-cols-2 gap-6">
                    <div class="command-panel rounded-xl p-6">
                        <h3 class="text-lg font-semibold text-white mb-4">DETECTION PERFORMANCE</h3>
                        <div class="space-y-4">
                            <div>
                                <div class="flex justify-between text-sm mb-1">
                                    <span class="text-gray-400">Accuracy Rate</span>
                                    <span class="text-emerald-400 font-command">97.8%</span>
                                </div>
                                <div class="w-full bg-command-700 rounded-full h-2">
                                    <div class="bg-emerald-500 h-2 rounded-full" style="width: 97.8%"></div>
                                </div>
                            </div>
                            <div>
                                <div class="flex justify-between text-sm mb-1">
                                    <span class="text-gray-400">Response Time</span>
                                    <span class="text-safety-400 font-command">1.2s</span>
                                </div>
                                <div class="w-full bg-command-700 rounded-full h-2">
                                    <div class="bg-safety-500 h-2 rounded-full" style="width: 85%"></div>
                                </div>
                            </div>
                            <div>
                                <div class="flex justify-between text-sm mb-1">
                                    <span class="text-gray-400">False Positive Rate</span>
                                    <span class="text-warning-400 font-command">1.1%</span>
                                </div>
                                <div class="w-full bg-command-700 rounded-full h-2">
                                    <div class="bg-warning-500 h-2 rounded-full" style="width: 11%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="command-panel rounded-xl p-6">
                        <h3 class="text-lg font-semibold text-white mb-4">SYSTEM METRICS</h3>
                        <div class="space-y-4">
                            <div class="flex justify-between items-center">
                                <span class="text-gray-400">CPU Usage</span>
                                <span class="text-emerald-400 font-command">23%</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-gray-400">Memory Usage</span>
                                <span class="text-safety-400 font-command">2.1GB</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-gray-400">Network Latency</span>
                                <span class="text-emerald-400 font-command">12ms</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-gray-400">Frames Processed</span>
                                <span class="text-white font-command">2,847,392</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderDetectionSettings() {
        return `
            <div class="p-6">
                <div class="mb-6">
                    <h2 class="text-2xl font-bold text-white mb-2">DETECTION SETTINGS</h2>
                    <p class="text-gray-400">Configure detection parameters and thresholds</p>
                </div>
                
                <div class="space-y-6">
                    <div class="command-panel rounded-xl p-6">
                        <h3 class="text-lg font-semibold text-white mb-4">CONFIDENCE THRESHOLDS</h3>
                        <div class="space-y-6">
                            ${this.renderThresholdSlider('P1 - IMMEDIATE ALERT', 'immediate_alert', 95, 'emergency')}
                            ${this.renderThresholdSlider('P2 - REVIEW QUEUE', 'review_queue', 85, 'warning')}
                            ${this.renderThresholdSlider('P4 - LOG ONLY', 'log_only', 70, 'safety')}
                        </div>
                    </div>
                    
                    <div class="command-panel rounded-xl p-6">
                        <h3 class="text-lg font-semibold text-white mb-4">ENVIRONMENTAL SETTINGS</h3>
                        <div class="grid grid-cols-2 gap-6">
                            <div class="space-y-4">
                                <label class="flex items-center justify-between">
                                    <span class="text-gray-300">Fog Compensation</span>
                                    <input type="checkbox" checked class="w-5 h-5 text-fire-500 bg-command-700 border-command-600 rounded focus:ring-fire-500">
                                </label>
                                <label class="flex items-center justify-between">
                                    <span class="text-gray-300">Adaptive Thresholds</span>
                                    <input type="checkbox" checked class="w-5 h-5 text-fire-500 bg-command-700 border-command-600 rounded focus:ring-fire-500">
                                </label>
                                <label class="flex items-center justify-between">
                                    <span class="text-gray-300">Night Mode Enhancement</span>
                                    <input type="checkbox" class="w-5 h-5 text-fire-500 bg-command-700 border-command-600 rounded focus:ring-fire-500">
                                </label>
                            </div>
                            <div class="space-y-4">
                                <label class="flex items-center justify-between">
                                    <span class="text-gray-300">Motion Detection</span>
                                    <input type="checkbox" checked class="w-5 h-5 text-fire-500 bg-command-700 border-command-600 rounded focus:ring-fire-500">
                                </label>
                                <label class="flex items-center justify-between">
                                    <span class="text-gray-300">Audio Alerts</span>
                                    <input type="checkbox" checked class="w-5 h-5 text-fire-500 bg-command-700 border-command-600 rounded focus:ring-fire-500">
                                </label>
                                <label class="flex items-center justify-between">
                                    <span class="text-gray-300">Debug Mode</span>
                                    <input type="checkbox" class="w-5 h-5 text-fire-500 bg-command-700 border-command-600 rounded focus:ring-fire-500">
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderThresholdSlider(label, id, value, colorScheme) {
        return `
            <div>
                <div class="flex justify-between items-center mb-2">
                    <label class="text-sm font-semibold text-${colorScheme}-400 uppercase tracking-wider">${label}</label>
                    <span class="text-xl font-command text-white">${value}%</span>
                </div>
                <div class="relative">
                    <input type="range" min="50" max="100" value="${value}" 
                           class="w-full h-2 bg-command-700 rounded-lg appearance-none cursor-pointer"
                           data-action="update-threshold" data-id="${id}">
                    <div class="absolute top-0 left-0 h-2 bg-gradient-to-r from-${colorScheme}-600 to-${colorScheme}-400 rounded-lg" 
                         style="width: ${value}%"></div>
                </div>
                <div class="text-xs text-gray-500 mt-1">Adjust sensitivity for ${label.toLowerCase()}</div>
            </div>
        `;
    }

    renderSystemHealth() {
        return `
            <div class="p-6">
                <div class="mb-6">
                    <h2 class="text-2xl font-bold text-white mb-2">SYSTEM HEALTH</h2>
                    <p class="text-gray-400">Monitor system performance and diagnostics</p>
                </div>
                
                <div class="grid grid-cols-3 gap-6">
                    <div class="command-panel rounded-xl p-6">
                        <h3 class="text-lg font-semibold text-emerald-400 mb-4">OPERATIONAL STATUS</h3>
                        <div class="space-y-3">
                            ${this.renderStatusItem('Detection Engine', 'ONLINE', 'emerald')}
                            ${this.renderStatusItem('Camera Network', 'ONLINE', 'emerald')}
                            ${this.renderStatusItem('Alert System', 'ONLINE', 'emerald')}
                            ${this.renderStatusItem('Database', 'ONLINE', 'emerald')}
                        </div>
                    </div>
                    
                    <div class="command-panel rounded-xl p-6">
                        <h3 class="text-lg font-semibold text-safety-400 mb-4">PERFORMANCE</h3>
                        <div class="space-y-3">
                            ${this.renderMetricItem('CPU Usage', '23%', 'good')}
                            ${this.renderMetricItem('Memory', '2.1GB', 'good')}
                            ${this.renderMetricItem('Storage', '45%', 'good')}
                            ${this.renderMetricItem('Network', '12ms', 'excellent')}
                        </div>
                    </div>
                    
                    <div class="command-panel rounded-xl p-6">
                        <h3 class="text-lg font-semibold text-warning-400 mb-4">MAINTENANCE</h3>
                        <div class="space-y-3">
                            <div class="flex justify-between items-center">
                                <span class="text-gray-300">Last Update</span>
                                <span class="text-xs font-command text-gray-400">2 days ago</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-gray-300">Next Maintenance</span>
                                <span class="text-xs font-command text-gray-400">in 5 days</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-gray-300">Data Retention</span>
                                <span class="text-xs font-command text-gray-400">30 days</span>
                            </div>
                            <button class="w-full bg-warning-500 hover:bg-warning-600 text-white py-2 rounded-lg text-sm font-semibold transition-colors mt-4">
                                RUN DIAGNOSTICS
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderStatusItem(label, status, color) {
        return `
            <div class="flex items-center justify-between">
                <span class="text-sm text-gray-300">${label}</span>
                <div class="flex items-center space-x-2">
                    <div class="w-2 h-2 bg-${color}-500 rounded-full animate-slow-pulse"></div>
                    <span class="text-xs font-command text-${color}-400">${status}</span>
                </div>
            </div>
        `;
    }

    renderMetricItem(label, value, status) {
        const colors = {
            excellent: 'emerald',
            good: 'safety',
            warning: 'warning',
            critical: 'emergency'
        };
        const color = colors[status] || 'gray';
        
        return `
            <div class="flex items-center justify-between">
                <span class="text-sm text-gray-300">${label}</span>
                <span class="text-xs font-command text-${color}-400">${value}</span>
            </div>
        `;
    }

    handleAction(action, id) {
        switch (action) {
            case 'acknowledge-alert':
                this.acknowledgeAlert(id);
                break;
            case 'clear-alerts':
                this.clearAllAlerts();
                break;
            case 'update-threshold':
                // Handle threshold updates
                break;
        }
    }

    acknowledgeAlert(alertId) {
        const alert = this.alertData.find(a => a.id === alertId);
        if (alert) {
            alert.status = 'acknowledged';
            this.updateAlertDisplays();
        }
    }

    clearAllAlerts() {
        this.alertData = [];
        this.updateAlertDisplays();
        this.updateActivityFeed();
    }

    updateClock() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', { 
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        const timeElement = document.getElementById('current-time');
        if (timeElement && timeElement.textContent !== timeString) {
            timeElement.textContent = timeString;
        }
    }

    updateAlertDisplays() {
        const activeAlerts = this.alertData.filter(alert => alert.status === 'active').length;
        const alertCountElement = document.getElementById('alert-count');
        if (alertCountElement && alertCountElement.textContent !== activeAlerts.toString()) {
            alertCountElement.textContent = activeAlerts;
        }

        // Update incidents list only if in incidents view
        if (this.currentView === 'incidents') {
            const incidentsList = document.getElementById('incidents-list');
            if (incidentsList) {
                const newContent = this.alertData.length === 0 ? `
                    <div class="text-center text-gray-500 py-12">
                        <div class="w-16 h-16 bg-emerald-500 rounded-full mx-auto mb-4 flex items-center justify-center">
                            <div class="w-8 h-8 bg-white rounded"></div>
                        </div>
                        <p class="text-lg font-semibold text-emerald-400">ALL CLEAR</p>
                        <p class="text-sm">No active incidents detected</p>
                    </div>
                ` : this.alertData.map(alert => this.renderIncidentItem(alert)).join('');
                
                if (incidentsList.innerHTML !== newContent) {
                    incidentsList.innerHTML = newContent;
                }
            }
        }
    }

    renderIncidentItem(alert) {
        const alertColors = {
            'P1': { bg: 'emergency', text: 'CRITICAL ALERT' },
            'P2': { bg: 'warning', text: 'REVIEW REQUIRED' },
            'P4': { bg: 'safety', text: 'LOGGED EVENT' }
        };
        
        const config = alertColors[alert.alert_level] || { bg: 'gray', text: 'UNKNOWN' };
        const timestamp = new Date(alert.timestamp * 1000).toLocaleTimeString();
        
        return `
            <div class="bg-command-700 rounded-lg p-4 border-l-4 border-${config.bg}-500">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-4">
                        <div class="bg-${config.bg}-500 text-white px-3 py-1 rounded-full text-xs font-semibold font-command">
                            ${alert.alert_level}
                        </div>
                        <div>
                            <div class="font-semibold text-white">${alert.camera_id}</div>
                            <div class="text-sm text-gray-400">${config.text}</div>
                        </div>
                    </div>
                    <div class="text-right">
                        <div class="text-lg font-command text-${config.bg}-400">${(alert.confidence * 100).toFixed(1)}%</div>
                        <div class="text-xs text-gray-500">${timestamp}</div>
                    </div>
                    <button data-action="acknowledge-alert" data-id="${alert.id}" 
                            class="bg-fire-500 hover:bg-fire-600 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors">
                        ${alert.status === 'active' ? 'ACKNOWLEDGE' : 'ACKNOWLEDGED'}
                    </button>
                </div>
            </div>
        `;
    }

    updateActivityFeed() {
        // Only update if in command view
        if (this.currentView !== 'command') return;
        
        const activityFeed = document.getElementById('activity-feed');
        if (!activityFeed) return;

        const newContent = this.alertData.length === 0 ? `
            <div class="text-center text-gray-500 py-8">
                <div class="w-12 h-12 bg-command-700 rounded-full mx-auto mb-3 flex items-center justify-center">
                    <div class="w-6 h-6 bg-command-600 rounded"></div>
                </div>
                <p>Monitoring all camera feeds...</p>
                <p class="text-sm">Alerts will appear here in real-time</p>
            </div>
        ` : this.alertData.slice(0, 5).map(alert => {
            const timestamp = new Date(alert.timestamp * 1000).toLocaleTimeString();
            const alertColors = {
                'P1': 'emergency',
                'P2': 'warning', 
                'P4': 'safety'
            };
            const color = alertColors[alert.alert_level] || 'gray';
            
            return `
                <div class="flex items-center space-x-4 p-3 bg-command-700 rounded-lg">
                    <div class="w-3 h-3 bg-${color}-500 rounded-full animate-slow-pulse"></div>
                    <div class="flex-1">
                        <div class="flex items-center justify-between">
                            <span class="font-semibold text-white">${alert.camera_id}</span>
                            <span class="text-xs text-gray-400 font-command">${timestamp}</span>
                        </div>
                        <div class="text-sm text-gray-400">
                            ${alert.alert_level} Alert - ${(alert.confidence * 100).toFixed(1)}% confidence
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        if (activityFeed.innerHTML !== newContent) {
            activityFeed.innerHTML = newContent;
        }
    }

    startRealTimeUpdates() {
        // Simulate real-time data updates
        setInterval(() => {
            this.simulateNewAlert();
        }, 5000); // Every 5 seconds
        
        // Update activity feed
        setInterval(() => {
            this.updateActivityFeed();
        }, 1000);
    }

    simulateNewAlert() {
        if (Math.random() < 0.1) { // Reduced to 10% chance every 5 seconds
            const cameras = ['CAM_001', 'CAM_002', 'CAM_003'];
            const levels = ['P1', 'P2', 'P4'];
            const confidences = [0.97, 0.89, 0.74];
            
            const randomIndex = Math.floor(Math.random() * 3);
            
            const newAlert = {
                id: `alert_${Date.now()}`,
                timestamp: Date.now() / 1000,
                camera_id: cameras[randomIndex],
                alert_level: levels[randomIndex],
                confidence: confidences[randomIndex],
                status: 'active'
            };
            
            this.alertData.unshift(newAlert);
            
            // Keep only last 25 alerts (reduced memory usage)
            if (this.alertData.length > 25) {
                this.alertData = this.alertData.slice(0, 25);
            }
            
            this.scheduleUpdate(() => {
                this.updateAlertDisplays();
                this.updateActivityFeed();
            });
        }
    }

    // Performance optimization methods
    scheduleUpdate(callback) {
        this.pendingUpdates.add(callback);
        if (!this.updateScheduled) {
            this.updateScheduled = true;
            requestAnimationFrame(() => {
                this.pendingUpdates.forEach(update => update());
                this.pendingUpdates.clear();
                this.updateScheduled = false;
            });
        }
    }

    pauseUpdates() {
        this.intervals.forEach(interval => clearInterval(interval));
        this.intervals = [];
    }

    resumeUpdates() {
        if (this.intervals.length === 0) {
            this.intervals.push(setInterval(() => this.updateClock(), 1000));
            this.intervals.push(setInterval(() => {
                if (!document.hidden) {
                    this.simulateNewAlert();
                }
            }, 5000));
            this.intervals.push(setInterval(() => {
                if (!document.hidden) {
                    this.scheduleUpdate(() => this.updateActivityFeed());
                }
            }, 2000));
        }
    }

    cleanup() {
        this.pauseUpdates();
        this.pendingUpdates.clear();
    }
}

// Initialize the command center when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.sentinelCommand = new SentinelCommandCenter();
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        if (window.sentinelCommand) {
            window.sentinelCommand.cleanup();
        }
    });
});