import { useState, useCallback } from 'react';

export const useSystemStatus = () => {
  const [systemStatus, setSystemStatus] = useState({
    cameras: 3,
    activeAlerts: 0,
    uptime: 99.9,
    systemHealth: 'optimal',
    detectionEngine: 'online',
    cameraNetwork: 'online',
    alertSystem: 'online'
  });

  const updateStatus = useCallback((updates) => {
    setSystemStatus(current => ({
      ...current,
      ...updates
    }));
  }, []);

  return {
    systemStatus,
    updateStatus
  };
};