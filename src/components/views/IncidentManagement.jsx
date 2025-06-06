import React, { useMemo } from 'react';

const AlertItem = ({ alert, onAcknowledge }) => {
  const alertColors = {
    'P1': { bg: 'emergency', text: 'CRITICAL ALERT' },
    'P2': { bg: 'warning', text: 'REVIEW REQUIRED' },
    'P4': { bg: 'safety', text: 'LOGGED EVENT' }
  };
  
  const config = alertColors[alert.alert_level] || { bg: 'gray', text: 'UNKNOWN' };
  const timestamp = new Date(alert.timestamp * 1000).toLocaleTimeString();
  
  return (
    <div className={`bg-command-700 rounded-lg p-4 border-l-4 border-${config.bg}-500`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className={`bg-${config.bg}-500 text-white px-3 py-1 rounded-full text-xs font-semibold font-command`}>
            {alert.alert_level}
          </div>
          <div>
            <div className="font-semibold text-white">{alert.camera_id}</div>
            <div className="text-sm text-gray-400">{config.text}</div>
          </div>
        </div>
        <div className="text-right">
          <div className={`text-lg font-command text-${config.bg}-400`}>
            {(alert.confidence * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500">{timestamp}</div>
        </div>
        <button 
          onClick={() => onAcknowledge(alert.id)}
          className="bg-fire-500 hover:bg-fire-600 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors hover-lift"
        >
          {alert.status === 'active' ? 'ACKNOWLEDGE' : 'ACKNOWLEDGED'}
        </button>
      </div>
    </div>
  );
};

const AllClearState = () => (
  <div className="text-center text-gray-500 py-12">
    <div className="w-16 h-16 bg-emerald-500 rounded-full mx-auto mb-4 flex items-center justify-center">
      <div className="w-8 h-8 bg-white rounded"></div>
    </div>
    <p className="text-lg font-semibold text-emerald-400">ALL CLEAR</p>
    <p className="text-sm">No active incidents detected</p>
  </div>
);

const IncidentManagement = ({ alerts, onClearAlerts, onAcknowledgeAlert }) => {
  const activeIncidents = useMemo(() => 
    alerts.filter(alert => alert.status === 'active'),
    [alerts]
  );

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">INCIDENT MANAGEMENT</h2>
        <p className="text-gray-400">Active alerts and incident response</p>
      </div>
      
      <div className="command-panel rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">ACTIVE INCIDENTS</h3>
          {activeIncidents.length > 0 && (
            <button 
              onClick={onClearAlerts}
              className="bg-fire-500 hover:bg-fire-600 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors hover-lift"
            >
              ACKNOWLEDGE ALL
            </button>
          )}
        </div>
        <div className="space-y-3">
          {activeIncidents.length === 0 ? (
            <AllClearState />
          ) : (
            activeIncidents.map(alert => (
              <AlertItem 
                key={alert.id} 
                alert={alert} 
                onAcknowledge={onAcknowledgeAlert}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default React.memo(IncidentManagement);