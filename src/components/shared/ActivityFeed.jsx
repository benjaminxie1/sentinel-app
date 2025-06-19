import React, { useMemo } from 'react';

const ActivityItem = ({ alert }) => {
  const timestamp = new Date(alert.timestamp * 1000).toLocaleTimeString();
  const alertColors = {
    'P1': 'emergency',
    'P2': 'warning', 
    'P4': 'safety'
  };
  const color = alertColors[alert.alert_level] || 'gray';
  
  return (
    <div className="flex items-center space-x-4 p-3 bg-gray-800/50 rounded-lg">
      <div className={`w-3 h-3 bg-${color}-500 rounded-full`}></div>
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <span className="font-semibold text-gray-100">{alert.camera_id}</span>
          <span className="text-xs text-gray-400 font-command">{timestamp}</span>
        </div>
        <div className="text-sm text-gray-400">
          {alert.alert_level} Alert - {(alert.confidence * 100).toFixed(1)}% confidence
        </div>
      </div>
    </div>
  );
};

const EmptyState = ({ connectionStatus }) => {
  if (connectionStatus && !connectionStatus.isConnected) {
    return (
      <div className="text-center text-gray-400 py-8">
        <div className="w-12 h-12 bg-emergency-600 rounded-full mx-auto mb-3 flex items-center justify-center">
          <div className="w-6 h-6 bg-emergency-400 rounded animate-pulse"></div>
        </div>
        <p className="text-emergency-400">Connection Lost</p>
        <p className="text-sm">Attempting to reconnect...</p>
      </div>
    );
  }
  
  return (
    <div className="text-center text-gray-400 py-8">
      <div className="w-12 h-12 bg-gray-800 rounded-full mx-auto mb-3 flex items-center justify-center">
        <div className="w-6 h-6 bg-gray-700 rounded"></div>
      </div>
      <p>Monitoring all camera feeds...</p>
      <p className="text-sm">Alerts will appear here in real-time</p>
    </div>
  );
};

const ActivityFeed = ({ alerts, isVisible, maxItems = 5, connectionStatus }) => {
  // Memoized recent alerts for performance
  const recentAlerts = useMemo(() => 
    alerts.slice(0, maxItems),
    [alerts, maxItems]
  );

  return (
    <div className="command-panel rounded-xl p-6">
      <h3 className="text-lg font-semibold text-gray-100 mb-4 flex items-center space-x-2">
        <div className="w-5 h-5 bg-success-500 rounded"></div>
        <span>LIVE ACTIVITY FEED</span>
      </h3>
      <div className="space-y-3 max-h-80 overflow-auto">
        {recentAlerts.length === 0 ? (
          <EmptyState connectionStatus={connectionStatus} />
        ) : (
          recentAlerts.map(alert => (
            <ActivityItem key={alert.id} alert={alert} />
          ))
        )}
      </div>
    </div>
  );
};

export default React.memo(ActivityFeed);