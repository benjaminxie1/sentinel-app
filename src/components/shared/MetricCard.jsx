import React from 'react';

const MetricCard = ({ title, value, color, description, indicator }) => {
  return (
    <div className="command-panel rounded-xl p-6">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
          {title}
        </h3>
        {indicator && (
          <div className={`w-3 h-3 bg-${color}-500 rounded-full animate-slow-pulse`}></div>
        )}
      </div>
      <div className={`text-3xl font-bold font-command text-${color}-400 mb-1`}>
        {value}
      </div>
      <div className="text-xs text-gray-500">{description}</div>
    </div>
  );
};

export default React.memo(MetricCard);