import { useState, useCallback, useEffect, useRef } from 'react';

export const useAlertSystem = () => {
  const [alerts, setAlerts] = useState([]);
  const intervalRef = useRef(null);
  const maxAlerts = 25; // Reduced for performance

  // Optimized alert addition
  const addAlert = useCallback((newAlert) => {
    setAlerts(current => {
      const updated = [newAlert, ...current].slice(0, maxAlerts);
      return updated;
    });
  }, []);

  // Clear all alerts
  const clearAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  // Acknowledge single alert
  const acknowledgeAlert = useCallback((alertId) => {
    setAlerts(current => 
      current.map(alert => 
        alert.id === alertId 
          ? { ...alert, status: 'acknowledged' }
          : alert
      )
    );
  }, []);

  // Simulate new alerts (reduced frequency for performance)
  useEffect(() => {
    const simulateAlert = () => {
      if (Math.random() < 0.08) { // 8% chance every 5 seconds
        const cameras = ['CAM_001', 'CAM_002', 'CAM_003'];
        const levels = ['P1', 'P2', 'P4'];
        const confidences = [0.97, 0.89, 0.74];
        
        const randomIndex = Math.floor(Math.random() * 3);
        
        const newAlert = {
          id: `alert_${Date.now()}`,
          timestamp: Date.now() / 1000,
          camera_id: cameras[randomIndex],
          alert_level: levels[randomIndex],
          confidence: confidences[randomIndex],
          status: 'active'
        };
        
        addAlert(newAlert);
      }
    };

    // Only run simulation when page is visible
    const runSimulation = () => {
      if (!document.hidden) {
        simulateAlert();
      }
    };

    intervalRef.current = setInterval(runSimulation, 5000);
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [addAlert]);

  return {
    alerts,
    addAlert,
    clearAlerts,
    acknowledgeAlert
  };
};