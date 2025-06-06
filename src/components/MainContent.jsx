import React, { Suspense, lazy } from 'react';

// Lazy load view components for better performance
const CommandCenter = lazy(() => import('./views/CommandCenter'));
const SurveillanceGrid = lazy(() => import('./views/SurveillanceGrid'));
const IncidentManagement = lazy(() => import('./views/IncidentManagement'));
const AnalyticsCenter = lazy(() => import('./views/AnalyticsCenter'));
const DetectionSettings = lazy(() => import('./views/DetectionSettings'));
const SystemHealth = lazy(() => import('./views/SystemHealth'));

const LoadingSpinner = () => (
  <div className="flex items-center justify-center h-full">
    <div className="w-8 h-8 fire-gradient rounded-lg flex items-center justify-center animate-slow-pulse">
      <div className="w-4 h-4 bg-white rounded-sm"></div>
    </div>
  </div>
);

const MainContent = ({ 
  currentView, 
  alerts, 
  systemStatus, 
  onClearAlerts, 
  onAcknowledgeAlert,
  isVisible 
}) => {
  const renderView = () => {
    const commonProps = {
      alerts,
      systemStatus,
      onClearAlerts,
      onAcknowledgeAlert,
      isVisible
    };

    switch (currentView) {
      case 'command':
        return <CommandCenter {...commonProps} />;
      case 'surveillance':
        return <SurveillanceGrid {...commonProps} />;
      case 'incidents':
        return <IncidentManagement {...commonProps} />;
      case 'analytics':
        return <AnalyticsCenter {...commonProps} />;
      case 'settings':
        return <DetectionSettings {...commonProps} />;
      case 'system':
        return <SystemHealth {...commonProps} />;
      default:
        return <CommandCenter {...commonProps} />;
    }
  };

  return (
    <main className="flex-1 overflow-auto">
      <Suspense fallback={<LoadingSpinner />}>
        {renderView()}
      </Suspense>
    </main>
  );
};

export default React.memo(MainContent);