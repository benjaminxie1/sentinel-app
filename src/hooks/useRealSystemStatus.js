import { useState, useCallback, useEffect, useRef } from 'react';
import { useTauriCommand, useTauriEvent } from './useTauriApi';

export const useRealSystemStatus = () => {
  const [systemStatus, setSystemStatus] = useState({
    cameras: 0,
    activeAlerts: 0,
    uptime: 0,
    systemHealth: 'starting',
    detectionEngine: 'starting',
    cameraNetwork: 'starting',
    alertSystem: 'starting',
    backendRunning: false,
    pythonPid: null
  });

  const intervalRef = useRef(null);
  const errorCountRef = useRef(0);
  const lastSuccessRef = useRef(Date.now());
  const debounceRef = useRef(null);
  
  // Tauri commands
  const { execute: getSystemStatus } = useTauriCommand('get_system_status');
  const { execute: getCameraFeeds } = useTauriCommand('get_camera_feeds');
  const { execute: getDashboardData } = useTauriCommand('get_dashboard_data');

  // Debounced status update function
  const updateStatusDebounced = useCallback((updates) => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    
    debounceRef.current = setTimeout(() => {
      setSystemStatus(current => ({
        ...current,
        ...updates
      }));
    }, 100); // 100ms debounce
  }, []);

  // Listen for real-time updates
  useTauriEvent('real-time-update', useCallback((event) => {
    const data = event.payload;
    if (data && data.alerts) {
      // Update active alerts count
      const activeAlerts = data.alerts.recent_alerts 
        ? data.alerts.recent_alerts.filter(alert => !alert.acknowledged).length 
        : 0;
      
      const systemHealth = data.alerts.system_status?.health || 'optimal';
      
      updateStatusDebounced({
        activeAlerts,
        systemHealth: mapHealthStatus(systemHealth),
        detectionEngine: data.alerts.system_status?.detection_engine || 'online',
        alertSystem: 'online'
      });
    }
  }, [updateStatusDebounced]));

  // Helper function to map backend health status to frontend format
  const mapHealthStatus = (backendHealth) => {
    switch (backendHealth) {
      case 'healthy':
      case 'optimal': return 'optimal';
      case 'warning': return 'warning';
      case 'error':
      case 'critical': return 'critical';
      default: return 'unknown';
    }
  };

  // Fetch comprehensive system status
  const refreshSystemStatus = useCallback(async () => {
    try {
      // Get backend system status
      const systemData = await getSystemStatus();
      const cameraData = await getCameraFeeds();
      const dashboardData = await getDashboardData();

      if (systemData) {
        const updates = {
          backendRunning: systemData.backend_running,
          pythonPid: systemData.python_pid,
          uptime: systemData.uptime || 0
        };

        // Camera information
        if (cameraData) {
          updates.cameras = cameraData.active_cameras || 0;
          updates.cameraNetwork = cameraData.active_cameras > 0 ? 'online' : 'offline';
        }

        // Alert information from dashboard
        if (dashboardData && dashboardData.alerts) {
          updates.activeAlerts = dashboardData.alerts.recent_alerts 
            ? dashboardData.alerts.recent_alerts.filter(alert => !alert.acknowledged).length 
            : 0;
          
          const systemHealth = dashboardData.alerts.system_status?.health || 'optimal';
          updates.systemHealth = mapHealthStatus(systemHealth);
          updates.detectionEngine = dashboardData.alerts.system_status?.detection_engine || 'online';
          updates.alertSystem = 'online';
        }

        // Overall system health assessment
        if (systemData.backend_running) {
          updates.detectionEngine = updates.detectionEngine || 'online';
        } else {
          updates.detectionEngine = 'offline';
          updates.systemHealth = 'critical';
          updates.cameraNetwork = 'offline';
          updates.alertSystem = 'offline';
        }

        setSystemStatus(current => ({
          ...current,
          ...updates
        }));

        // Reset error count on success
        errorCountRef.current = 0;
        lastSuccessRef.current = Date.now();
      }
    } catch (error) {
      console.error('Failed to refresh system status:', error);
      
      // Increment error count
      errorCountRef.current += 1;
      const timeSinceLastSuccess = Date.now() - lastSuccessRef.current;
      
      // Only set to critical if we've had multiple errors over a longer period
      // This prevents flashing "critical" during brief network hiccups
      if (errorCountRef.current >= 3 && timeSinceLastSuccess > 15000) {
        setSystemStatus(current => ({
          ...current,
          systemHealth: 'critical',
          detectionEngine: 'offline',
          cameraNetwork: 'offline',
          alertSystem: 'offline',
          backendRunning: false
        }));
      } else if (errorCountRef.current >= 2) {
        // Show warning after 2 errors
        setSystemStatus(current => ({
          ...current,
          systemHealth: 'warning'
        }));
      }
      // Don't change status on first error - could be temporary
    }
  }, [getSystemStatus, getCameraFeeds, getDashboardData]);

  // Periodic status refresh
  useEffect(() => {
    // Initial status check
    refreshSystemStatus();

    // Set up periodic refresh (every 10 seconds to reduce load)
    intervalRef.current = setInterval(refreshSystemStatus, 10000);
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [refreshSystemStatus]);

  // Manual status update function (for compatibility)
  const updateStatus = useCallback((updates) => {
    setSystemStatus(current => ({
      ...current,
      ...updates
    }));
  }, []);

  return {
    systemStatus,
    updateStatus,
    refreshSystemStatus
  };
};