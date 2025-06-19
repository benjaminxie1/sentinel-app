import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { motion } from 'framer-motion';
import { Camera, Signal, AlertTriangle, Eye, Play, RefreshCw, Plus, Search, X, Trash2 } from 'lucide-react';
import clsx from 'clsx';
import { useCameraManager } from '../../hooks/useCameraManager';
import { useNotifications } from '../../hooks/useNotifications';
import AddCameraModal from '../shared/AddCameraModal';
import { RemoveCameraConfirmDialog } from '../shared/ConfirmDialog';

// Frame URL validation utility for security
const isValidFrameUrl = (url) => {
  if (!url || typeof url !== 'string') return false;
  
  // Check for valid base64 data URL format
  if (url.startsWith('data:image/')) {
    return /^data:image\/(jpeg|jpg|png|gif|webp);base64,[A-Za-z0-9+/]+=*$/.test(url);
  }
  
  // Check for valid HTTP/HTTPS URLs (for RTSP streams converted to HTTP)
  if (url.startsWith('http://') || url.startsWith('https://')) {
    try {
      const urlObj = new URL(url);
      return ['localhost', '127.0.0.1'].includes(urlObj.hostname) || 
             urlObj.hostname.match(/^192\.168\.\d+\.\d+$/) ||
             urlObj.hostname.match(/^10\.\d+\.\d+\.\d+$/) ||
             urlObj.hostname.match(/^172\.(1[6-9]|2\d|3[01])\.\d+\.\d+$/);
    } catch {
      return false;
    }
  }
  
  return false;
};

const CameraFeed = ({ camera, frame, onRefresh, onRemove, delay = 0 }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showRemoveConfirm, setShowRemoveConfirm] = useState(false);
  
  const getStatusConfig = () => {
    switch (camera.status) {
      case 'online':
        return { color: 'success', icon: Signal, bg: 'bg-success-500' };
      case 'warning': 
        return { color: 'warning', icon: AlertTriangle, bg: 'bg-warning-500' };
      default:
        return { color: 'gray', icon: Camera, bg: 'bg-gray-500' };
    }
  };
  
  const statusConfig = getStatusConfig();
  const StatusIcon = statusConfig.icon;
  const hasValidFrame = frame && frame.url && isValidFrameUrl(frame.url);
  const hasInvalidFrame = frame && frame.url && !isValidFrameUrl(frame.url);
  
  const formatLastUpdate = (timestamp) => {
    if (!timestamp) return 'Never';
    const now = Date.now() / 1000;
    const diff = now - timestamp;
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className="glass rounded-xl overflow-hidden hover:shadow-medium transition-all duration-300"
    >
      {/* Camera Header */}
      <div className="p-4 border-b border-gray-800 bg-gray-900/50">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-gray-100 font-mono">{camera.id}</h3>
            <p className="text-sm text-gray-400">{camera.location}</p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => onRefresh(camera.id)}
              className="p-1 rounded hover:bg-gray-800 transition-colors"
              title="Refresh feed"
            >
              <RefreshCw className="w-4 h-4 text-gray-400 hover:text-gray-200" />
            </button>
            <div className="flex items-center space-x-2">
              <div className={clsx('w-2 h-2 rounded-full', statusConfig.bg)} />
              <span className={clsx(
                'text-xs font-mono uppercase',
                statusConfig.color === 'success' ? 'text-success-400' :
                statusConfig.color === 'warning' ? 'text-warning-400' :
                'text-gray-400'
              )}>
                {camera.status}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Camera Feed Area */}
      <div className="bg-gray-950 h-48 flex items-center justify-center relative group">
        {hasValidFrame ? (
          <>
            <img 
              src={frame.url} 
              alt={`Camera ${camera.id} feed`}
              className="w-full h-full object-cover"
            />
            
            {/* Live indicator */}
            <div className="absolute top-2 right-2 bg-success-500 text-white text-xs px-2 py-1 rounded-full font-mono animate-pulse">
              LIVE
            </div>
            
            {/* Expand button overlay */}
            <motion.button
              initial={{ opacity: 0 }}
              whileHover={{ opacity: 1, scale: 1.1 }}
              className="absolute inset-0 flex items-center justify-center bg-black/20 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-all"
              onClick={() => setIsExpanded(true)}
            >
              <div className="w-12 h-12 bg-fire-500 rounded-full flex items-center justify-center">
                <Eye className="w-6 h-6 text-white" />
              </div>
            </motion.button>
          </>
        ) : (
          <>
            {/* No feed placeholder */}
            <div className="text-center">
              <div className="w-16 h-16 bg-gray-800 rounded-lg mx-auto mb-3 flex items-center justify-center">
                <StatusIcon className={clsx(
                  'w-8 h-8',
                  statusConfig.color === 'success' ? 'text-success-400' :
                  statusConfig.color === 'warning' ? 'text-warning-400' :
                  'text-gray-500'
                )} />
              </div>
              <p className="text-gray-400 text-sm">
                {hasInvalidFrame ? 'Invalid frame data' :
                 camera.status === 'online' ? 'Loading feed...' : 
                 camera.status === 'warning' ? 'Connection issues' :
                 'Camera offline'}
              </p>
            </div>
            
            {/* Retry button for online cameras */}
            {camera.status === 'online' && (
              <motion.button
                initial={{ opacity: 0 }}
                whileHover={{ opacity: 1, scale: 1.1 }}
                className="absolute inset-0 flex items-center justify-center bg-black/20 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-all"
                onClick={() => onRefresh(camera.id)}
              >
                <div className="w-12 h-12 bg-fire-500 rounded-full flex items-center justify-center">
                  <RefreshCw className="w-6 h-6 text-white" />
                </div>
              </motion.button>
            )}
          </>
        )}
      </div>

      {/* Camera Controls */}
      <div className="p-3 bg-gray-900/30 border-t border-gray-800">
        <div className="flex items-center justify-between">
          <div className="text-xs text-gray-500">
            <div>Last update: {formatLastUpdate(camera.lastFrameTime)}</div>
            <div className="mt-1">
              {camera.fps > 0 ? `${camera.fps} FPS` : 'No signal'} • {camera.resolution}
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button 
              className="btn-ghost text-xs py-1 px-2"
              onClick={() => setIsExpanded(true)}
            >
              <Eye className="w-3 h-3 mr-1" />
              View
            </button>
            <button 
              className="btn-ghost text-xs py-1 px-2 text-red-400 hover:text-red-300"
              onClick={() => setShowRemoveConfirm(true)}
            >
              <Trash2 className="w-3 h-3 mr-1" />
              Remove
            </button>
          </div>
        </div>
      </div>

      {/* Expanded view modal */}
      {isExpanded && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setIsExpanded(false)}
        >
          <motion.div
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0.9 }}
            className="bg-gray-900 rounded-xl overflow-hidden max-w-4xl w-full max-h-[90vh]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-4 border-b border-gray-800 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-100">{camera.id}</h3>
                <p className="text-sm text-gray-400">{camera.location}</p>
              </div>
              <button
                onClick={() => setIsExpanded(false)}
                className="text-gray-400 hover:text-gray-200"
              >
                ✕
              </button>
            </div>
            
            <div className="relative bg-black">
              {hasFrame ? (
                <img 
                  src={frame.url} 
                  alt={`Camera ${camera.id} expanded view`}
                  className="w-full h-auto max-h-[70vh] object-contain"
                />
              ) : (
                <div className="flex items-center justify-center h-96">
                  <div className="text-center text-gray-400">
                    <Camera className="w-16 h-16 mx-auto mb-4" />
                    <p>No feed available</p>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}

      {/* Remove confirmation modal */}
      <RemoveCameraConfirmDialog
        isOpen={showRemoveConfirm}
        onClose={() => setShowRemoveConfirm(false)}
        onConfirm={() => onRemove(camera.id)}
        cameraName={camera.name}
      />
    </motion.div>
  );
};

CameraFeed.propTypes = {
  camera: PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string,
    status: PropTypes.string.isRequired,
    rtsp_url: PropTypes.string,
    location: PropTypes.string
  }).isRequired,
  frame: PropTypes.shape({
    url: PropTypes.string,
    timestamp: PropTypes.number
  }),
  onRefresh: PropTypes.func.isRequired,
  onRemove: PropTypes.func.isRequired,
  delay: PropTypes.number
};

CameraFeed.defaultProps = {
  delay: 0
};

const SurveillanceGridReal = () => {
  const {
    cameras,
    frames,
    isLoading,
    refreshCameras,
    getCameraCurrentFrame,
    discoverNewCameras,
    addNewCamera,
    testCameraConnection,
    removeCameraById,
    getCameraStats
  } = useCameraManager();

  const [isDiscovering, setIsDiscovering] = useState(false);
  const [isAddCameraModalOpen, setIsAddCameraModalOpen] = useState(false);
  
  const notifications = useNotifications();
  const stats = getCameraStats();

  const handleRefreshCamera = async (cameraId) => {
    await getCameraCurrentFrame(cameraId);
  };

  const handleDiscoverCameras = async () => {
    setIsDiscovering(true);
    const loadingToast = notifications.showLoading('Scanning network for cameras...');
    
    try {
      const discovered = await discoverNewCameras(10);
      notifications.dismiss(loadingToast);
      notifications.operations.cameraDiscovered(discovered?.length || 0);
      console.log('Discovered cameras:', discovered);
    } catch (error) {
      console.error('Camera discovery failed:', error);
      notifications.dismiss(loadingToast);
      notifications.showError(`Camera discovery failed: ${error.message}`);
    } finally {
      setIsDiscovering(false);
    }
  };

  const handleAddCamera = async (cameraConfig) => {
    const result = await addNewCamera(cameraConfig);
    if (!result.success) {
      throw new Error(result.message);
    }
    return result;
  };

  const handleTestConnection = async (cameraConfig) => {
    return await testCameraConnection(cameraConfig);
  };

  const handleDiscoverCamerasForModal = async (timeout) => {
    return await discoverNewCameras(timeout);
  };

  const handleRemoveCamera = async (cameraId) => {
    const camera = cameras.find(c => c.id === cameraId);
    const cameraName = camera?.name || cameraId;
    
    const loadingToast = notifications.showLoading(`Removing camera ${cameraName}...`);
    
    try {
      const result = await removeCameraById(cameraId);
      notifications.dismiss(loadingToast);
      
      if (result.success) {
        notifications.operations.cameraRemoved(cameraName);
      } else {
        console.error('Failed to remove camera:', result.message);
        notifications.showError(`Failed to remove camera ${cameraName}: ${result.message}`);
      }
    } catch (error) {
      console.error('Error removing camera:', error);
      notifications.dismiss(loadingToast);
      notifications.showError(`Error removing camera ${cameraName}: ${error.message}`);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="p-8 space-y-8 overflow-y-auto h-full"
    >
      {/* Page Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold gradient-text mb-2">Surveillance Grid</h1>
          <p className="text-gray-400">Real-time camera monitoring and management</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button
            onClick={handleDiscoverCameras}
            disabled={isDiscovering}
            className="btn-ghost text-sm py-2 px-4 flex items-center"
          >
            <Search className={clsx('w-4 h-4 mr-2', isDiscovering && 'animate-spin')} />
            {isDiscovering ? 'Discovering...' : 'Discover Cameras'}
          </button>
          
          <button
            onClick={refreshCameras}
            disabled={isLoading}
            className="btn-ghost text-sm py-2 px-4 flex items-center"
          >
            <RefreshCw className={clsx('w-4 h-4 mr-2', isLoading && 'animate-spin')} />
            Refresh All
          </button>
          
          <button 
            onClick={() => setIsAddCameraModalOpen(true)}
            className="btn-primary text-sm py-2 px-4 flex items-center"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Camera
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-xl p-6"
        >
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-success-500 to-success-600">
              <Camera className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-2xl font-bold text-success-400">{stats.online}</p>
              <p className="text-sm text-gray-400">Online</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass rounded-xl p-6"
        >
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-warning-500 to-warning-600">
              <AlertTriangle className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-2xl font-bold text-warning-400">{stats.warning}</p>
              <p className="text-sm text-gray-400">Warning</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass rounded-xl p-6"
        >
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-error-500 to-error-600">
              <Camera className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-2xl font-bold text-error-400">{stats.offline}</p>
              <p className="text-sm text-gray-400">Offline</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass rounded-xl p-6"
        >
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-fire-500 to-fire-600">
              <Eye className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-2xl font-bold text-fire-400">{stats.total}</p>
              <p className="text-sm text-gray-400">Total Feeds</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Loading State */}
      {isLoading && cameras.length === 0 && (
        <div className="text-center py-12">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-gray-400" />
          <p className="text-gray-400">Loading camera feeds...</p>
        </div>
      )}

      {/* Camera Grid */}
      {cameras.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {cameras.map((camera, index) => (
            <CameraFeed 
              key={camera.id} 
              camera={camera}
              frame={frames[camera.id]}
              onRefresh={handleRefreshCamera}
              onRemove={handleRemoveCamera}
              delay={index * 0.1}
            />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && cameras.length === 0 && (
        <div className="text-center py-12">
          <Camera className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-semibold text-gray-300 mb-2">No cameras configured</h3>
          <p className="text-gray-400 mb-6">Add RTSP cameras to start monitoring</p>
          <button 
            onClick={() => setIsAddCameraModalOpen(true)}
            className="btn-primary"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Your First Camera
          </button>
        </div>
      )}

      {/* Add Camera Modal */}
      <AddCameraModal
        isOpen={isAddCameraModalOpen}
        onClose={() => setIsAddCameraModalOpen(false)}
        onAddCamera={handleAddCamera}
        onTestConnection={handleTestConnection}
        onDiscoverCameras={handleDiscoverCamerasForModal}
      />
    </motion.div>
  );
};

export default React.memo(SurveillanceGridReal);