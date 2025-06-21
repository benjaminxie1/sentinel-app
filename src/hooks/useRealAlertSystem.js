import { useState, useCallback, useEffect, useRef } from 'react';
import { useTauriCommand, useTauriEvent } from './useTauriApi';
import { useNotifications } from './useNotifications';

export const useRealAlertSystem = () => {
  const [alerts, setAlerts] = useState([]);
  const [dashboardData, setDashboardData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastError, setLastError] = useState(null);
  const intervalRef = useRef(null);
  const retryCountRef = useRef(0);
  const maxRetries = 3;
  
  const notifications = useNotifications();
  
  // Tauri commands
  const { execute: fetchDashboardData } = useTauriCommand('get_dashboard_data');
  const { execute: acknowledgeAlertCommand } = useTauriCommand('acknowledge_alert');
  const { execute: startBackend } = useTauriCommand('start_python_backend');

  // Note: Python backend is now auto-started by Tauri on app launch
  // No need to manually start it here anymore

  // Listen for real-time updates from backend
  useTauriEvent('real-time-update', useCallback((event) => {
    const data = event.payload;
    if (data && data.alerts) {
      setDashboardData(data);
      
      // Extract alerts from dashboard data
      if (data.alerts.recent_alerts) {
        const formattedAlerts = data.alerts.recent_alerts.map((alert, index) => {
          // Alert ID validation handled silently
          return {
          id: alert.id || `missing_id_${Date.now()}_${index}`,
          timestamp: alert.timestamp || Date.now() / 1000,
          camera_id: alert.camera_id || 'Unknown',
          alert_level: alert.alert_level?.value || alert.alert_level || 'P4',
          confidence: alert.confidence || 0,
          status: alert.acknowledged ? 'acknowledged' : 'active',
          location: alert.location || 'Unknown',
          description: alert.description || `Alert from ${alert.camera_id}`
        };
      });
        
        setAlerts(formattedAlerts);
      }
    }
  }, []));

  // Periodic data refresh as backup
  useEffect(() => {
    const refreshData = async () => {
      try {
        const data = await fetchDashboardData();
        if (data && data.alerts) {
          setDashboardData(data);
          setIsConnected(true);
          setLastError(null);
          retryCountRef.current = 0;
          
          // Extract and format alerts
          if (data.alerts.recent_alerts) {
            const formattedAlerts = data.alerts.recent_alerts.map((alert, index) => {
              // Alert ID validation handled silently
              return {
              id: alert.id || `missing_id_${Date.now()}_${index}`,
              timestamp: alert.timestamp || Date.now() / 1000,
              camera_id: alert.camera_id || 'Unknown',
              alert_level: alert.alert_level?.value || alert.alert_level || 'P4',
              confidence: alert.confidence || 0,
              status: alert.acknowledged ? 'acknowledged' : 'active',
              location: alert.location || 'Unknown',
              description: alert.description || `Alert from ${alert.camera_id}`
            };
          });
            
            setAlerts(formattedAlerts);
          }
        }
      } catch (error) {
        console.error('Failed to refresh dashboard data:', error);
        setLastError(error.message);
        retryCountRef.current++;
        
        if (retryCountRef.current <= maxRetries) {
          notifications.showError(`Connection issue, retrying... (${retryCountRef.current}/${maxRetries})`);
          
          // Exponential backoff retry
          setTimeout(() => {
            refreshData();
          }, Math.pow(2, retryCountRef.current) * 1000);
        } else {
          setIsConnected(false);
          notifications.showError('Lost connection to backend. Please check system status.');
        }
      }
    };

    // Initial fetch
    refreshData();

    // Set up periodic refresh (every 15 seconds as backup)
    intervalRef.current = setInterval(refreshData, 15000);
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchDashboardData]);

  // Add alert (for compatibility, mainly used by real-time updates)
  const addAlert = useCallback((newAlert) => {
    setAlerts(current => {
      // Avoid duplicates
      const exists = current.some(alert => alert.id === newAlert.id);
      if (exists) return current;
      
      return [newAlert, ...current].slice(0, 50); // Keep last 50 alerts
    });
  }, []);

  // Clear all alerts (UI only, not persistent)
  const clearAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  // Acknowledge alert - communicates with backend
  const acknowledgeAlert = useCallback(async (alertId) => {
    try {
      const success = await acknowledgeAlertCommand({ alert_id: alertId });
      
      if (success) {
        // Optimistically update UI
        setAlerts(current => 
          current.map(alert => 
            alert.id === alertId 
              ? { ...alert, status: 'acknowledged' }
              : alert
          )
        );
        notifications.operations.alertAcknowledged();
      } else {
        throw new Error('Backend returned failure response');
      }
    } catch (error) {
      console.error('Error acknowledging alert:', error);
      notifications.showError(`Failed to acknowledge alert: ${error.message}`);
      
      // Retry mechanism for critical operations
      const retryAcknowledge = async () => {
        try {
          const retrySuccess = await acknowledgeAlertCommand({ alert_id: alertId });
          if (retrySuccess) {
            setAlerts(current => 
              current.map(alert => 
                alert.id === alertId 
                  ? { ...alert, status: 'acknowledged' }
                  : alert
              )
            );
            notifications.operations.alertAcknowledged();
          }
        } catch (retryError) {
          notifications.showError('Unable to acknowledge alert. Please try manually.');
        }
      };
      
      // Auto-retry after 2 seconds
      setTimeout(retryAcknowledge, 2000);
    }
  }, [acknowledgeAlertCommand, notifications]);

  return {
    alerts,
    dashboardData,
    addAlert,
    clearAlerts,
    acknowledgeAlert,
    isConnected,
    lastError,
    retryCount: retryCountRef.current
  };
};