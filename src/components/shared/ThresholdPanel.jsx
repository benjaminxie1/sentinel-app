import React, { useState, useEffect } from 'react';
import { useTauriCommand } from '../../hooks/useTauriApi';

const ThresholdItem = ({ label, value, color }) => {
  const isLoading = value === 'Loading...';
  const displayValue = isLoading ? 'Loading...' : `${value}%`;
  const progressWidth = isLoading ? 0 : value;
  
  return (
    <div className="bg-gray-800/50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <span className={`text-sm font-semibold text-${color}-400 uppercase tracking-wider`}>
          {label}
        </span>
        <span className="text-xl font-command text-gray-100">{displayValue}</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-2">
        <div 
          className={`bg-gradient-to-r from-${color}-600 to-${color}-400 h-2 rounded-full transition-all duration-300`}
          style={{ width: `${progressWidth}%` }}
        ></div>
      </div>
      <div className="text-xs text-gray-400 mt-2">
        {label === 'P1 - IMMEDIATE' && 'Automatic dispatch'}
        {label === 'P2 - REVIEW' && 'Human verification'}
        {label === 'P4 - LOG' && 'Data collection'}
      </div>
    </div>
  );
};

const ThresholdPanel = () => {
  const [config, setConfig] = useState({});
  const { execute: getDashboardData } = useTauriCommand('get_dashboard_data');
  
  // Fetch dashboard data to get current thresholds
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const data = await getDashboardData();
        console.log('Dashboard data received:', data); // Debug log
        if (data?.config) {
          console.log('Config data:', data.config); // Debug log
          setConfig(data.config);
        } else {
          console.warn('No config data in response:', data);
        }
      } catch (error) {
        console.error('Failed to fetch threshold config:', error);
      }
    };
    
    fetchConfig();
    
    // Also fetch periodically to keep data fresh
    const interval = setInterval(fetchConfig, 5000);
    return () => clearInterval(interval);
  }, [getDashboardData]);
  
  // Use dynamic thresholds from backend or show loading state
  const detectionThresholds = config.detection_thresholds || {};
  console.log('Detection thresholds:', detectionThresholds); // Debug log
  
  const thresholds = [
    { 
      label: 'P1 - IMMEDIATE', 
      value: typeof detectionThresholds.immediate_alert === 'number' ? Math.round(detectionThresholds.immediate_alert * 100) : 'Loading...', 
      color: 'error' 
    },
    { 
      label: 'P2 - REVIEW', 
      value: typeof detectionThresholds.review_queue === 'number' ? Math.round(detectionThresholds.review_queue * 100) : 'Loading...', 
      color: 'warning' 
    },
    { 
      label: 'P4 - LOG', 
      value: typeof detectionThresholds.log_only === 'number' ? Math.round(detectionThresholds.log_only * 100) : 'Loading...', 
      color: 'success' 
    }
  ];

  return (
    <div className="command-panel rounded-xl p-6">
      <h3 className="text-lg font-semibold text-gray-100 mb-4 flex items-center space-x-2">
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