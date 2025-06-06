import React, { useState, useCallback, useEffect, useRef } from 'react';
import Header from './Header';
import Navigation from './Navigation';
import MainContent from './MainContent';
import { useAlertSystem } from '../hooks/useAlertSystem';
import { useSystemStatus } from '../hooks/useSystemStatus';

const App = () => {
  const [currentView, setCurrentView] = useState('command');
  const [isVisible, setIsVisible] = useState(true);
  
  // Custom hooks for data management
  const { alerts, addAlert, clearAlerts, acknowledgeAlert } = useAlertSystem();
  const { systemStatus, updateStatus } = useSystemStatus();
  
  // Page visibility optimization
  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsVisible(!document.hidden);
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, []);

  // Optimized view switching
  const handleViewChange = useCallback((newView) => {
    if (newView !== currentView) {
      setCurrentView(newView);
    }
  }, [currentView]);

  // Optimized action handlers
  const handleClearAlerts = useCallback(() => {
    clearAlerts();
  }, [clearAlerts]);

  const handleAcknowledgeAlert = useCallback((alertId) => {
    acknowledgeAlert(alertId);
  }, [acknowledgeAlert]);

  return (
    <div className="h-screen flex flex-col bg-command-900 text-white overflow-hidden">
      <Header 
        systemStatus={systemStatus}
        alertCount={alerts.filter(a => a.status === 'active').length}
      />
      
      <div className="flex-1 flex overflow-hidden">
        <Navigation 
          currentView={currentView}
          onViewChange={handleViewChange}
          systemStatus={systemStatus}
        />
        
        <MainContent
          currentView={currentView}
          alerts={alerts}
          systemStatus={systemStatus}
          onClearAlerts={handleClearAlerts}
          onAcknowledgeAlert={handleAcknowledgeAlert}
          isVisible={isVisible}
        />
      </div>
    </div>
  );
};

export default App;