import React, { useMemo } from 'react';
import MetricCard from '../shared/MetricCard';
import ThresholdPanel from '../shared/ThresholdPanel';
import ActivityFeed from '../shared/ActivityFeed';

const CommandCenter = ({ alerts, systemStatus, isVisible }) => {
  // Memoized calculations for performance
  const activeAlertsCount = useMemo(() => 
    alerts.filter(alert => alert.status === 'active').length,
    [alerts]
  );

  const threatLevel = useMemo(() => {
    if (activeAlertsCount === 0) return { level: 'LOW', color: 'emerald', description: 'No active threats detected' };
    if (activeAlertsCount < 3) return { level: 'MEDIUM', color: 'warning', description: 'Monitoring active alerts' };
    return { level: 'HIGH', color: 'emergency', description: 'Multiple threats detected' };
  }, [activeAlertsCount]);

  const metrics = [
    {
      title: 'THREAT LEVEL',
      value: threatLevel.level,
      color: threatLevel.color,
      description: threatLevel.description,
      indicator: true
    },
    {
      title: 'ACTIVE CAMERAS',
      value: systemStatus.cameras,
      color: 'fire',
      description: 'All systems operational',
      indicator: true
    },
    {
      title: 'ALERTS TODAY',
      value: activeAlertsCount,
      color: 'warning',
      description: 'Last 24 hours',
      indicator: true
    },
    {
      title: 'SYSTEM UPTIME',
      value: `${systemStatus.uptime}%`,
      color: 'safety',
      description: 'Operational excellence',
      indicator: true
    }
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Critical Metrics Row */}
      <div className="grid grid-cols-4 gap-6">
        {metrics.map((metric, index) => (
          <MetricCard key={index} {...metric} />
        ))}
      </div>

      {/* Detection Thresholds Panel */}
      <ThresholdPanel />

      {/* Live Activity Feed */}
      <ActivityFeed 
        alerts={alerts}
        isVisible={isVisible}
        maxItems={5}
      />
    </div>
  );
};

export default React.memo(CommandCenter);