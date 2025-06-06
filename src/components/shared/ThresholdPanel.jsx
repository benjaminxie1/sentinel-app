import React from 'react';

const ThresholdItem = ({ label, value, color }) => (
  <div className="bg-command-700 rounded-lg p-4">
    <div className="flex items-center justify-between mb-3">
      <span className={`text-sm font-semibold text-${color}-400 uppercase tracking-wider`}>
        {label}
      </span>
      <span className="text-xl font-command text-white">{value}%</span>
    </div>
    <div className="w-full bg-command-600 rounded-full h-2">
      <div 
        className={`bg-gradient-to-r from-${color}-600 to-${color}-400 h-2 rounded-full`}
        style={{ width: `${value}%` }}
      ></div>
    </div>
    <div className="text-xs text-gray-400 mt-2">
      {label === 'P1 - IMMEDIATE' && 'Automatic dispatch'}
      {label === 'P2 - REVIEW' && 'Human verification'}
      {label === 'P4 - LOG' && 'Data collection'}
    </div>
  </div>
);

const ThresholdPanel = () => {
  const thresholds = [
    { label: 'P1 - IMMEDIATE', value: 95, color: 'emergency' },
    { label: 'P2 - REVIEW', value: 85, color: 'warning' },
    { label: 'P4 - LOG', value: 70, color: 'safety' }
  ];

  return (
    <div className="command-panel rounded-xl p-6">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
        <div className="w-5 h-5 fire-gradient rounded"></div>
        <span>DETECTION PARAMETERS</span>
      </h3>
      <div className="grid grid-cols-3 gap-6">
        {thresholds.map((threshold, index) => (
          <ThresholdItem key={index} {...threshold} />
        ))}
      </div>
    </div>
  );
};

export default React.memo(ThresholdPanel);