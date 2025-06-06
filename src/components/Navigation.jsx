import React from 'react';

const NavigationButton = ({ isActive, view, icon, label, onClick }) => (
  <button
    onClick={() => onClick(view)}
    className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors hover-lift ${
      isActive
        ? 'bg-fire-500 text-white'
        : 'text-gray-300 hover:text-white hover:bg-command-700'
    }`}
  >
    <div className="w-4 h-4 bg-current rounded-sm"></div>
    <span>{label}</span>
  </button>
);

const StatusItem = ({ label, status, value }) => {
  const statusColors = {
    online: 'emerald',
    active: 'emerald',
    ready: 'emerald'
  };
  
  const color = statusColors[status.toLowerCase()] || 'gray';
  
  return (
    <div className="flex justify-between items-center">
      <span className="text-sm text-gray-300">{label}</span>
      <div className="flex items-center space-x-2">
        <div className={`w-2 h-2 bg-${color}-500 rounded-full animate-slow-pulse`}></div>
        <span className={`text-xs font-command text-${color}-400`}>{value}</span>
      </div>
    </div>
  );
};

const Navigation = ({ currentView, onViewChange, systemStatus }) => {
  const operationsItems = [
    { view: 'command', label: 'Command Center' },
    { view: 'surveillance', label: 'Surveillance Grid' },
    { view: 'incidents', label: 'Incident Management' },
    { view: 'analytics', label: 'Analytics Center' }
  ];

  const configItems = [
    { view: 'settings', label: 'Detection Settings' },
    { view: 'system', label: 'System Health' }
  ];

  return (
    <nav className="w-64 bg-command-800 border-r border-command-600 p-4 space-y-2">
      <div className="mb-6">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          OPERATIONS
        </h2>
        <div className="space-y-1">
          {operationsItems.map((item) => (
            <NavigationButton
              key={item.view}
              isActive={currentView === item.view}
              view={item.view}
              label={item.label}
              onClick={onViewChange}
            />
          ))}
        </div>
      </div>

      <div className="mb-6">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          CONFIGURATION
        </h2>
        <div className="space-y-1">
          {configItems.map((item) => (
            <NavigationButton
              key={item.view}
              isActive={currentView === item.view}
              view={item.view}
              label={item.label}
              onClick={onViewChange}
            />
          ))}
        </div>
      </div>

      {/* System Status Panel */}
      <div className="command-panel rounded-lg p-4 mt-8">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          SYSTEM STATUS
        </h3>
        <div className="space-y-3">
          <StatusItem 
            label="Detection Engine" 
            status={systemStatus.detectionEngine}
            value="ACTIVE"
          />
          <StatusItem 
            label="Camera Grid" 
            status={systemStatus.cameraNetwork}
            value={`${systemStatus.cameras}/3 ONLINE`}
          />
          <StatusItem 
            label="Alert System" 
            status={systemStatus.alertSystem}
            value="READY"
          />
        </div>
      </div>
    </nav>
  );
};

export default React.memo(Navigation);