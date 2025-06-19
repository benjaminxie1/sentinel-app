import React from 'react';

const MetricCard = ({ title, value, color, description, indicator }) => {
  const colorClasses = {
    fire: 'text-fire-400',
    safety: 'text-success-400', 
    warning: 'text-warning-400',
    emergency: 'text-error-400',
    error: 'text-error-400',
    success: 'text-success-400',
    gray: 'text-gray-400'
  };

  const bgColorClasses = {
    fire: 'bg-fire-500',
    safety: 'bg-success-500', 
    warning: 'bg-warning-500',
    emergency: 'bg-error-500',
    error: 'bg-error-500',
    success: 'bg-success-500',
    gray: 'bg-gray-500'
  };

  return (
    <div className="metric-card">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
          {title}
        </h3>
        {indicator && (
          <div className={`w-3 h-3 ${bgColorClasses[color] || bgColorClasses.gray} rounded-full`}></div>
        )}
      </div>
      <div className={`text-3xl font-bold font-mono mb-1 ${colorClasses[color] || colorClasses.gray}`}>
        {value}
      </div>
      <div className="text-xs text-gray-400">{description}</div>
    </div>
  );
};

export default React.memo(MetricCard);