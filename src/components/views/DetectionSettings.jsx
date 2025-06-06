import React, { useState } from 'react';

const ThresholdSlider = ({ label, id, value, colorScheme, onChange }) => (
  <div>
    <div className="flex justify-between items-center mb-2">
      <label className={`text-sm font-semibold text-${colorScheme}-400 uppercase tracking-wider`}>
        {label}
      </label>
      <span className="text-xl font-command text-white">{value}%</span>
    </div>
    <div className="relative">
      <input 
        type="range" 
        min="50" 
        max="100" 
        value={value}
        onChange={(e) => onChange(id, parseInt(e.target.value))}
        className="w-full h-2 bg-command-700 rounded-lg appearance-none cursor-pointer"
      />
      <div 
        className={`absolute top-0 left-0 h-2 bg-gradient-to-r from-${colorScheme}-600 to-${colorScheme}-400 rounded-lg`}
        style={{ width: `${value}%` }}
      ></div>
    </div>
    <div className="text-xs text-gray-500 mt-1">
      Adjust sensitivity for {label.toLowerCase()}
    </div>
  </div>
);

const ToggleSetting = ({ label, checked, onChange }) => (
  <label className="flex items-center justify-between">
    <span className="text-gray-300">{label}</span>
    <input 
      type="checkbox" 
      checked={checked}
      onChange={(e) => onChange(e.target.checked)}
      className="w-5 h-5 text-fire-500 bg-command-700 border-command-600 rounded focus:ring-fire-500"
    />
  </label>
);

const DetectionSettings = () => {
  const [thresholds, setThresholds] = useState({
    immediate_alert: 95,
    review_queue: 85,
    log_only: 70
  });

  const [settings, setSettings] = useState({
    fogCompensation: true,
    adaptiveThresholds: true,
    nightMode: false,
    motionDetection: true,
    audioAlerts: true,
    debugMode: false
  });

  const handleThresholdChange = (id, value) => {
    setThresholds(prev => ({ ...prev, [id]: value }));
  };

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const thresholdConfigs = [
    { label: 'P1 - IMMEDIATE ALERT', id: 'immediate_alert', value: thresholds.immediate_alert, colorScheme: 'emergency' },
    { label: 'P2 - REVIEW QUEUE', id: 'review_queue', value: thresholds.review_queue, colorScheme: 'warning' },
    { label: 'P4 - LOG ONLY', id: 'log_only', value: thresholds.log_only, colorScheme: 'safety' }
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">DETECTION SETTINGS</h2>
        <p className="text-gray-400">Configure detection parameters and thresholds</p>
      </div>
      
      <div className="space-y-6">
        <div className="command-panel rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">CONFIDENCE THRESHOLDS</h3>
          <div className="space-y-6">
            {thresholdConfigs.map((config) => (
              <ThresholdSlider 
                key={config.id}
                {...config}
                onChange={handleThresholdChange}
              />
            ))}
          </div>
        </div>
        
        <div className="command-panel rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">ENVIRONMENTAL SETTINGS</h3>
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-4">
              <ToggleSetting 
                label="Fog Compensation"
                checked={settings.fogCompensation}
                onChange={(value) => handleSettingChange('fogCompensation', value)}
              />
              <ToggleSetting 
                label="Adaptive Thresholds"
                checked={settings.adaptiveThresholds}
                onChange={(value) => handleSettingChange('adaptiveThresholds', value)}
              />
              <ToggleSetting 
                label="Night Mode Enhancement"
                checked={settings.nightMode}
                onChange={(value) => handleSettingChange('nightMode', value)}
              />
            </div>
            <div className="space-y-4">
              <ToggleSetting 
                label="Motion Detection"
                checked={settings.motionDetection}
                onChange={(value) => handleSettingChange('motionDetection', value)}
              />
              <ToggleSetting 
                label="Audio Alerts"
                checked={settings.audioAlerts}
                onChange={(value) => handleSettingChange('audioAlerts', value)}
              />
              <ToggleSetting 
                label="Debug Mode"
                checked={settings.debugMode}
                onChange={(value) => handleSettingChange('debugMode', value)}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default React.memo(DetectionSettings);