import React from 'react';

const StatusItem = ({ label, status, color }) => (
  <div className="flex items-center justify-between">
    <span className="text-sm text-gray-300">{label}</span>
    <div className="flex items-center space-x-2">
      <div className={`w-2 h-2 bg-${color}-500 rounded-full animate-slow-pulse`}></div>
      <span className={`text-xs font-command text-${color}-400`}>{status}</span>
    </div>
  </div>
);

const MetricItem = ({ label, value, status }) => {
  const colors = {
    excellent: 'emerald',
    good: 'safety',
    warning: 'warning',
    critical: 'emergency'
  };
  const color = colors[status] || 'gray';
  
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-300">{label}</span>
      <span className={`text-xs font-command text-${color}-400`}>{value}</span>
    </div>
  );
};

const MaintenanceItem = ({ label, value }) => (
  <div className="flex justify-between items-center">
    <span className="text-gray-300">{label}</span>
    <span className="text-xs font-command text-gray-400">{value}</span>
  </div>
);

const SystemHealth = () => {
  const operationalStatus = [
    { label: 'Detection Engine', status: 'ONLINE', color: 'emerald' },
    { label: 'Camera Network', status: 'ONLINE', color: 'emerald' },
    { label: 'Alert System', status: 'ONLINE', color: 'emerald' },
    { label: 'Database', status: 'ONLINE', color: 'emerald' }
  ];

  const performanceMetrics = [
    { label: 'CPU Usage', value: '23%', status: 'good' },
    { label: 'Memory', value: '2.1GB', status: 'good' },
    { label: 'Storage', value: '45%', status: 'good' },
    { label: 'Network', value: '12ms', status: 'excellent' }
  ];

  const maintenanceInfo = [
    { label: 'Last Update', value: '2 days ago' },
    { label: 'Next Maintenance', value: 'in 5 days' },
    { label: 'Data Retention', value: '30 days' }
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">SYSTEM HEALTH</h2>
        <p className="text-gray-400">Monitor system performance and diagnostics</p>
      </div>
      
      <div className="grid grid-cols-3 gap-6">
        <div className="command-panel rounded-xl p-6">
          <h3 className="text-lg font-semibold text-emerald-400 mb-4">OPERATIONAL STATUS</h3>
          <div className="space-y-3">
            {operationalStatus.map((item, index) => (
              <StatusItem key={index} {...item} />
            ))}
          </div>
        </div>
        
        <div className="command-panel rounded-xl p-6">
          <h3 className="text-lg font-semibold text-safety-400 mb-4">PERFORMANCE</h3>
          <div className="space-y-3">
            {performanceMetrics.map((item, index) => (
              <MetricItem key={index} {...item} />
            ))}
          </div>
        </div>
        
        <div className="command-panel rounded-xl p-6">
          <h3 className="text-lg font-semibold text-warning-400 mb-4">MAINTENANCE</h3>
          <div className="space-y-3">
            {maintenanceInfo.map((item, index) => (
              <MaintenanceItem key={index} {...item} />
            ))}
            <button className="w-full bg-warning-500 hover:bg-warning-600 text-white py-2 rounded-lg text-sm font-semibold transition-colors mt-4 hover-lift">
              RUN DIAGNOSTICS
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default React.memo(SystemHealth);