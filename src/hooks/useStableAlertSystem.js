import { useState, useCallback, useEffect, useRef } from 'react';
import { useTauriCommand, useTauriEvent } from './useTauriApi';
import { useNotifications } from './useNotifications';
import { useDelayedLoading } from './useDelayedLoading';

/**
 * Enhanced alert system with anti-flashing and graceful degradation
 * Designed for industrial fire safety where reliable alert handling is critical
 */
export const useStableAlertSystem = () => {
  const [alerts, setAlerts] = useState([]);
  const [dashboardData, setDashboardData] = useState(null);
  const [lastSuccessfulData, setLastSuccessfulData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastError, setLastError] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  const intervalRef = useRef(null);
  const retryCountRef = useRef(0);
  const lastSuccessRef = useRef(Date.now());
  const connectionStableRef = useRef(false);
  const maxRetries = 5; // Increased for industrial reliability
  
  const notifications = useNotifications();
  
  // Use delayed loading to prevent flashing connection status
  const { shouldShowLoading, isStale } = useDelayedLoading(isRefreshing, {
    delay: 300,        // Slightly longer delay for connection issues
    minDuration: 800,  // Keep connection indicators stable
    enableStaleData: true
  });
  
  // Tauri commands
  const { execute: fetchDashboardData } = useTauriCommand('get_dashboard_data');
  const { execute: acknowledgeAlertCommand } = useTauriCommand('acknowledge_alert');
  const { execute: startBackend } = useTauriCommand('start_python_backend');

  // Format alerts with enhanced error handling
  const formatAlerts = useCallback((rawAlerts) => {
    if (!Array.isArray(rawAlerts)) return [];
    
    return rawAlerts.map((alert, index) => {
      if (!alert.id) {
        console.error('Alert missing ID from backend:', alert);
      }
      return {
        id: alert.id || `alert_${Date.now()}_${index}`,
        timestamp: alert.timestamp || Date.now() / 1000,
        camera_id: alert.camera_id || 'Unknown',
        alert_level: alert.alert_level?.value || alert.alert_level || 'P4',
        confidence: alert.confidence || 0,
        status: alert.acknowledged ? 'acknowledged' : 'active',
        location: alert.location || 'Unknown',
        description: alert.description || `Alert from ${alert.camera_id || 'Unknown'}`
      };
    });
  }, []);

  // Enhanced real-time update handler
  useTauriEvent('real-time-update', useCallback((event) => {
    const data = event.payload;
    if (data && data.alerts) {
      // Mark connection as stable
      connectionStableRef.current = true;
      setIsConnected(true);
      setLastError(null);
      retryCountRef.current = 0;
      lastSuccessRef.current = Date.now();
      
      // Update dashboard data
      setDashboardData(data);
      setLastSuccessfulData(data);
      
      // Extract and format alerts
      if (data.alerts.recent_alerts) {
        const formattedAlerts = formatAlerts(data.alerts.recent_alerts);
        setAlerts(formattedAlerts);
      }
    }
  }, [formatAlerts]));

  // Enhanced data refresh with graceful degradation
  const refreshData = useCallback(async (isManualRefresh = false) => {
    // Only show loading state for manual refreshes or when connection is unstable
    if (isManualRefresh || !connectionStableRef.current) {
      setIsRefreshing(true);
    }

    try {
      const data = await fetchDashboardData();
      
      if (data && data.alerts) {
        // Success - update all state
        setDashboardData(data);
        setLastSuccessfulData(data);
        setIsConnected(true);
        setLastError(null);
        retryCountRef.current = 0;
        lastSuccessRef.current = Date.now();
        connectionStableRef.current = true;
        
        // Extract and format alerts
        if (data.alerts.recent_alerts) {
          const formattedAlerts = formatAlerts(data.alerts.recent_alerts);
          setAlerts(formattedAlerts);
        }
      } else {
        throw new Error('Invalid response format from backend');
      }
    } catch (error) {
      console.error('Failed to refresh dashboard data:', error);
      
      retryCountRef.current++;
      const timeSinceLastSuccess = Date.now() - lastSuccessRef.current;
      
      // Graceful degradation strategy
      if (retryCountRef.current <= 2) {
        // First few errors - keep current data, minimal user notification
        console.warn(`Connection issue ${retryCountRef.current}, retrying silently...`);
      } else if (retryCountRef.current <= maxRetries) {
        // Moderate errors - show warnings but keep data
        setLastError(error.message);
        connectionStableRef.current = false;
        
        if (isManualRefresh) {
          notifications.showError(`Connection issue, retrying... (${retryCountRef.current}/${maxRetries})`);
        }
        
        // Exponential backoff retry for manual refreshes
        if (isManualRefresh && retryCountRef.current < maxRetries) {
          setTimeout(() => {
            refreshData(true);
          }, Math.min(Math.pow(2, retryCountRef.current) * 1000, 10000)); // Cap at 10s
        }
      } else {
        // Extended failure - mark as disconnected but keep stale data
        if (timeSinceLastSuccess > 60000) { // Only after 1 minute of failures
          setIsConnected(false);
          connectionStableRef.current = false;
        }
        
        if (timeSinceLastSuccess > 300000) { // After 5 minutes, notify user
          notifications.showError('Extended connection loss. Using cached data. Please check system status.');
        }
      }
      
      // Use stale data strategy - don't clear alerts unless severely outdated
      if (lastSuccessfulData && timeSinceLastSuccess < 600000) { // Keep data for 10 minutes
        console.log('Using stale data due to connection issues');
        // Don't update UI - keep showing last successful data
      }
    } finally {
      setIsRefreshing(false);
    }
  }, [fetchDashboardData, formatAlerts, notifications, lastSuccessfulData]);

  // Initial setup and periodic refresh
  useEffect(() => {
    // Initial fetch
    refreshData(true);

    // Adaptive refresh interval based on connection stability
    const getRefreshInterval = () => {
      if (!connectionStableRef.current) return 5000;  // 5s when unstable
      if (retryCountRef.current > 0) return 10000;    // 10s after errors
      return 20000; // 20s when stable (longer than original for efficiency)
    };

    const scheduleNextRefresh = () => {
      if (intervalRef.current) {
        clearTimeout(intervalRef.current);
      }
      
      intervalRef.current = setTimeout(() => {
        refreshData(false); // Background refresh
        scheduleNextRefresh();
      }, getRefreshInterval());
    };

    scheduleNextRefresh();
    
    return () => {
      if (intervalRef.current) {
        clearTimeout(intervalRef.current);
      }
    };
  }, [refreshData]);

  // Enhanced add alert with deduplication
  const addAlert = useCallback((newAlert) => {
    setAlerts(current => {
      // Avoid duplicates by ID or by camera+timestamp similarity
      const existsById = current.some(alert => alert.id === newAlert.id);
      const existsBySimilarity = current.some(alert => 
        alert.camera_id === newAlert.camera_id && 
        Math.abs(alert.timestamp - newAlert.timestamp) < 5 // Within 5 seconds
      );
      
      if (existsById || existsBySimilarity) return current;
      
      return [newAlert, ...current].slice(0, 100); // Keep last 100 alerts
    });
  }, []);

  // Clear all alerts (UI only, not persistent)
  const clearAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  // Enhanced acknowledge alert with retry logic
  const acknowledgeAlert = useCallback(async (alertId) => {
    // Optimistically update UI immediately
    setAlerts(current => 
      current.map(alert => 
        alert.id === alertId 
          ? { ...alert, status: 'acknowledged' }
          : alert
      )
    );

    try {
      const success = await acknowledgeAlertCommand({ alert_id: alertId });
      
      if (success) {
        notifications.operations.alertAcknowledged();
      } else {
        throw new Error('Backend returned failure response');
      }
    } catch (error) {
      console.error('Error acknowledging alert:', error);
      
      // Revert optimistic update
      setAlerts(current => 
        current.map(alert => 
          alert.id === alertId 
            ? { ...alert, status: 'active' }
            : alert
        )
      );
      
      notifications.showError(`Failed to acknowledge alert: ${error.message}`);
      
      // Enhanced retry mechanism
      const retryAcknowledge = async (attempt = 1) => {
        if (attempt > 3) {
          notifications.showError('Unable to acknowledge alert after multiple attempts. Please try manually.');
          return;
        }
        
        try {
          await new Promise(resolve => setTimeout(resolve, attempt * 2000)); // Progressive delay
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
          } else {
            throw new Error('Retry failed');
          }
        } catch (retryError) {
          console.warn(`Acknowledge retry ${attempt} failed:`, retryError);
          if (attempt < 3) {
            retryAcknowledge(attempt + 1);
          } else {
            notifications.showError('Unable to acknowledge alert. Please try manually.');
          }
        }
      };
      
      retryAcknowledge();
    }
  }, [acknowledgeAlertCommand, notifications]);

  return {
    alerts,
    dashboardData: dashboardData || lastSuccessfulData, // Use stale data if needed
    addAlert,
    clearAlerts,
    acknowledgeAlert,
    isConnected,
    lastError,
    retryCount: retryCountRef.current,
    // Enhanced state info
    isRefreshing: shouldShowLoading,
    isStale: isStale || (dashboardData === null && lastSuccessfulData !== null),
    refreshData: () => refreshData(true),
    // Debug info
    _debug: {
      connectionStable: connectionStableRef.current,
      timeSinceLastSuccess: Date.now() - lastSuccessRef.current,
      hasStaleData: !!lastSuccessfulData,
      currentRetryCount: retryCountRef.current
    }
  };
};