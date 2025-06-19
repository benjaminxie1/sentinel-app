import React from 'react';

const NavigationButton = ({ isActive, view, icon, label, onClick }) => (
  <button
    onClick={() => onClick(view)}
    className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
      isActive
        ? 'bg-gray-800 text-gray-100 shadow-lg'
        : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
    }`}
  >
    <div className="w-4 h-4 bg-current rounded-sm"></div>
    <span>{label}</span>
  </button>
);

const StatusItem = ({ label, status, value }) => {
  const statusColors = {
    online: 'success',
    active: 'success',
    ready: 'success'
  };
  
  const color = statusColors[status.toLowerCase()] || 'gray';
  
  return (
    <div className="flex justify-between items-center">
      <span className="text-sm text-gray-400">{label}</span>
      <div className="flex items-center space-x-2">
        <div className={`w-2 h-2 bg-${color}-500 rounded-full`}></div>
        <span className={`text-xs font-mono text-${color}-400`}>{value}</span>
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
    { view: 'settings', label: 'Detection Settings' }
  ];

  return (
    <nav className="w-64 glass border-r border-gray-800 p-4 space-y-2">
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
      <div className="command-panel rounded-lg mt-8">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          SYSTEM STATUS
        </h3>
        <div className="space-y-3">
          <StatusItem 
            label="Detection Engine" 
            status={systemStatus.detectionEngine}
            value={systemStatus.detectionEngine === 'online' ? 'ACTIVE' : 'OFFLINE'}
          />
          <StatusItem 
            label="Camera Grid" 
            status={systemStatus.cameraNetwork}
            value={`${systemStatus.cameras}/${systemStatus.totalCameras || systemStatus.cameras} ONLINE`}
          />
          <StatusItem 
            label="Alert System" 
            status={systemStatus.alertSystem}
            value={systemStatus.alertSystem === 'ready' ? 'READY' : 'UNAVAILABLE'}
          />
        </div>
      </div>
    </nav>
  );
};

export default React.memo(Navigation);