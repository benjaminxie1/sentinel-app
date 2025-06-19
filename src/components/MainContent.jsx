import React, { Suspense, lazy } from 'react';
import PropTypes from 'prop-types';

// Lazy load view components for better performance
const CommandCenter = lazy(() => import('./views/CommandCenter'));
const SurveillanceGrid = lazy(() => import('./views/SurveillanceGridReal'));
const IncidentManagement = lazy(() => import('./views/IncidentManagement'));
const AnalyticsCenter = lazy(() => import('./views/AnalyticsCenter'));
const DetectionSettings = lazy(() => import('./views/DetectionSettingsReal'));

const LoadingSpinner = () => (
  <div className="flex items-center justify-center h-full">
    <div className="w-8 h-8 fire-gradient rounded-lg flex items-center justify-center">
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
  isVisible,
  connectionStatus
}) => {
  const renderView = () => {
    const commonProps = {
      alerts,
      systemStatus,
      onClearAlerts,
      onAcknowledgeAlert,
      isVisible,
      connectionStatus
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

MainContent.propTypes = {
  currentView: PropTypes.string.isRequired,
  alerts: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    status: PropTypes.string.isRequired,
    timestamp: PropTypes.number,
    message: PropTypes.string,
    severity: PropTypes.string
  })).isRequired,
  systemStatus: PropTypes.shape({
    backend_running: PropTypes.bool,
    python_pid: PropTypes.number,
    last_update: PropTypes.number,
    cameras_online: PropTypes.number,
    detection_active: PropTypes.bool
  }),
  onClearAlerts: PropTypes.func.isRequired,
  onAcknowledgeAlert: PropTypes.func.isRequired,
  isVisible: PropTypes.bool.isRequired,
  connectionStatus: PropTypes.shape({
    isConnected: PropTypes.bool.isRequired,
    lastError: PropTypes.string,
    retryCount: PropTypes.number
  }).isRequired
};

export default React.memo(MainContent);