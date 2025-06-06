import React from 'react';

const PerformanceMetric = ({ label, value, color }) => (
  <div>
    <div className="flex justify-between text-sm mb-1">
      <span className="text-gray-400">{label}</span>
      <span className={`text-${color}-400 font-command`}>{value}</span>
    </div>
    <div className="w-full bg-command-700 rounded-full h-2">
      <div 
        className={`bg-${color}-500 h-2 rounded-full`}
        style={{ width: typeof value === 'string' ? '85%' : `${value}%` }}
      ></div>
    </div>
  </div>
);

const SystemMetric = ({ label, value, color }) => (
  <div className="flex justify-between items-center">
    <span className="text-gray-400">{label}</span>
    <span className={`text-${color}-400 font-command`}>{value}</span>
  </div>
);

const AnalyticsCenter = () => {
  const performanceMetrics = [
    { label: 'Accuracy Rate', value: '97.8%', color: 'emerald' },
    { label: 'Response Time', value: '1.2s', color: 'safety' },
    { label: 'False Positive Rate', value: '1.1%', color: 'warning' }
  ];

  const systemMetrics = [
    { label: 'CPU Usage', value: '23%', color: 'emerald' },
    { label: 'Memory Usage', value: '2.1GB', color: 'safety' },
    { label: 'Network Latency', value: '12ms', color: 'emerald' },
    { label: 'Frames Processed', value: '2,847,392', color: 'white' }
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">ANALYTICS CENTER</h2>
        <p className="text-gray-400">Performance metrics and insights</p>
      </div>
      
      <div className="grid grid-cols-2 gap-6">
        <div className="command-panel rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">DETECTION PERFORMANCE</h3>
          <div className="space-y-4">
            {performanceMetrics.map((metric, index) => (
              <PerformanceMetric key={index} {...metric} />
            ))}
          </div>
        </div>
        
        <div className="command-panel rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">SYSTEM METRICS</h3>
          <div className="space-y-4">
            {systemMetrics.map((metric, index) => (
              <SystemMetric key={index} {...metric} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default React.memo(AnalyticsCenter);