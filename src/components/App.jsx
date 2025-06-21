import React, { useState, useCallback, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import Header from './Header';
import Navigation from './Navigation';
import MainContent from './MainContent';
import NotificationProvider from './shared/NotificationProvider';
import { useStableAlertSystem } from '../hooks/useStableAlertSystem';
import { useStableSystemStatus } from '../hooks/useStableSystemStatus';

const App = () => {
  const [currentView, setCurrentView] = useState('command');
  const [isVisible, setIsVisible] = useState(true);
  
  // Stable backend integration hooks with anti-flashing
  const { alerts, dashboardData, addAlert, clearAlerts, acknowledgeAlert, isConnected, lastError, retryCount } = useStableAlertSystem();
  const { systemStatus, updateStatus, refreshSystemStatus, isRefreshing, isStale } = useStableSystemStatus();
  
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
    <NotificationProvider>
      <div className="h-screen flex flex-col bg-gray-950 text-gray-100 overflow-hidden">
        <Header 
          systemStatus={systemStatus}
          alertCount={alerts.filter(a => a.status === 'active').length}
          isRefreshing={isRefreshing}
          isStale={isStale}
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
            connectionStatus={{ isConnected, lastError, retryCount }}
          />
        </div>
      </div>
    </NotificationProvider>
  );
};

export default App;