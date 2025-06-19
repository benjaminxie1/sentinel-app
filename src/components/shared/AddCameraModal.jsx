import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Camera, Wifi, TestTube, AlertCircle, CheckCircle, Loader, Info, Search } from 'lucide-react';
import { useNotifications } from '../../hooks/useNotifications';
import { validateCameraForm, getRTSPExamples } from '../../utils/validation';

const AddCameraModal = ({ isOpen, onClose, onAddCamera, onTestConnection, onDiscoverCameras, existingCameraIds = [] }) => {
  const [formData, setFormData] = useState({
    cameraId: '',
    rtspUrl: '',
    username: '',
    password: '',
    fps: 15
  });
  
  const [errors, setErrors] = useState({});
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [connectionTestResult, setConnectionTestResult] = useState(null);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [discoveredCameras, setDiscoveredCameras] = useState([]);
  const [showDiscovered, setShowDiscovered] = useState(false);
  const [showExamples, setShowExamples] = useState(false);
  
  const notifications = useNotifications();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
    
    // Clear connection test when URL changes
    if (name === 'rtspUrl' || name === 'username' || name === 'password') {
      setConnectionTestResult(null);
    }
    
    // Real-time validation for RTSP URL
    if (name === 'rtspUrl' && value.trim()) {
      const validation = validateCameraForm({ ...formData, [name]: value }, existingCameraIds);
      if (validation.errors.rtspUrl) {
        setErrors(prev => ({ ...prev, rtspUrl: validation.errors.rtspUrl }));
      }
    }
  };

  const validateForm = () => {
    const validation = validateCameraForm(formData, existingCameraIds);
    
    // Add FPS validation
    if (formData.fps < 1 || formData.fps > 60) {
      validation.errors.fps = 'FPS must be between 1 and 60';
      validation.isValid = false;
    }
    
    setErrors(validation.errors);
    return validation.isValid;
  };

  const handleTestConnection = async () => {
    if (!formData.rtspUrl.trim()) {
      setErrors(prev => ({ ...prev, rtspUrl: 'RTSP URL is required for testing' }));
      notifications.operations.validationError('RTSP URL is required for testing');
      return;
    }
    
    setIsTestingConnection(true);
    setConnectionTestResult(null);
    
    const loadingToast = notifications.showLoading('Testing camera connection...');
    
    try {
      const config = {
        rtspUrl: formData.rtspUrl,
        username: formData.username || null,
        password: formData.password || null
      };
      
      const result = await onTestConnection(config);
      setConnectionTestResult(result);
      
      notifications.dismiss(loadingToast);
      
      if (result.success) {
        notifications.operations.cameraTestSuccess(formData.cameraId || 'Camera');
      } else {
        notifications.operations.cameraTestFailed(formData.cameraId || 'Camera', result.message);
      }
    } catch (error) {
      notifications.dismiss(loadingToast);
      const result = {
        success: false,
        message: `Connection test failed: ${error.message}`
      };
      setConnectionTestResult(result);
      notifications.operations.cameraTestFailed(formData.cameraId || 'Camera', error.message);
    } finally {
      setIsTestingConnection(false);
    }
  };

  const handleDiscoverCameras = async () => {
    setIsDiscovering(true);
    setDiscoveredCameras([]);
    
    const loadingToast = notifications.showLoading('Scanning network for cameras...');
    
    try {
      const cameras = await onDiscoverCameras(10);
      setDiscoveredCameras(cameras || []);
      setShowDiscovered(true);
      
      notifications.dismiss(loadingToast);
      notifications.operations.cameraDiscovered(cameras?.length || 0);
    } catch (error) {
      console.error('Camera discovery failed:', error);
      setDiscoveredCameras([]);
      notifications.dismiss(loadingToast);
      notifications.showError(`Camera discovery failed: ${error.message}`);
    } finally {
      setIsDiscovering(false);
    }
  };

  const handleUseDiscoveredCamera = (camera) => {
    setFormData(prev => ({
      ...prev,
      rtspUrl: camera.rtspUrl,
      cameraId: `Camera_${camera.ip.replace(/\./g, '_')}`
    }));
    setShowDiscovered(false);
    setConnectionTestResult(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      notifications.operations.validationError('Please correct the form errors before submitting');
      return;
    }
    
    // Warn if connection wasn't tested
    if (!connectionTestResult || !connectionTestResult.success) {
      const proceed = window.confirm('Camera connection has not been successfully tested. Add camera anyway?');
      if (!proceed) {
        return;
      }
    }
    
    const loadingToast = notifications.showLoading(`Adding camera ${formData.cameraId}...`);
    
    try {
      const config = {
        cameraId: formData.cameraId.trim(),
        rtspUrl: formData.rtspUrl.trim(),
        username: formData.username.trim() || null,
        password: formData.password.trim() || null,
        fps: parseInt(formData.fps)
      };
      
      await onAddCamera(config);
      
      notifications.dismiss(loadingToast);
      notifications.operations.cameraAdded(config.cameraId);
      
      // Reset form and close modal
      setFormData({
        cameraId: '',
        rtspUrl: '',
        username: '',
        password: '',
        fps: 15
      });
      setErrors({});
      setConnectionTestResult(null);
      setDiscoveredCameras([]);
      setShowDiscovered(false);
      onClose();
      
    } catch (error) {
      notifications.dismiss(loadingToast);
      notifications.showError(`Failed to add camera: ${error.message}`);
      setErrors({ submit: `Failed to add camera: ${error.message}` });
    }
  };

  const handleClose = () => {
    setFormData({
      cameraId: '',
      rtspUrl: '',
      username: '',
      password: '',
      fps: 15
    });
    setErrors({});
    setConnectionTestResult(null);
    setDiscoveredCameras([]);
    setShowDiscovered(false);
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="glass rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-700">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-lg bg-gradient-to-br from-primary-500 to-primary-600">
                  <Camera className="w-5 h-5 text-white" />
                </div>
                <h2 className="text-xl font-semibold text-white">Add New Camera</h2>
              </div>
              <button
                onClick={handleClose}
                className="p-2 rounded-lg hover:bg-gray-700 transition-colors"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            {/* Discovery Section */}
            <div className="p-6 border-b border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-white">Camera Discovery</h3>
                <button
                  onClick={handleDiscoverCameras}
                  disabled={isDiscovering}
                  className="btn-secondary text-sm py-2 px-4 flex items-center disabled:opacity-50"
                >
                  {isDiscovering ? (
                    <Loader className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Wifi className="w-4 h-4 mr-2" />
                  )}
                  {isDiscovering ? 'Discovering...' : 'Discover Cameras'}
                </button>
              </div>
              
              {showDiscovered && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="space-y-2"
                >
                  {discoveredCameras.length > 0 ? (
                    discoveredCameras.map((camera, index) => (
                      <div
                        key={index}
                        className="glass rounded-lg p-3 flex items-center justify-between"
                      >
                        <div>
                          <div className="text-white font-medium">{camera.type}</div>
                          <div className="text-gray-400 text-sm">{camera.ip}</div>
                        </div>
                        <button
                          onClick={() => handleUseDiscoveredCamera(camera)}
                          className="btn-primary text-xs py-1 px-3"
                        >
                          Use
                        </button>
                      </div>
                    ))
                  ) : (
                    <div className="text-gray-400 text-center py-4">
                      No cameras discovered on the network
                    </div>
                  )}
                </motion.div>
              )}
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {/* Camera ID */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Camera ID *
                </label>
                <input
                  type="text"
                  name="cameraId"
                  value={formData.cameraId}
                  onChange={handleInputChange}
                  placeholder="e.g., Front_Door, Parking_Lot"
                  className={`input-field ${errors.cameraId ? 'border-red-500' : ''}`}
                />
                {errors.cameraId && (
                  <p className="text-red-400 text-sm mt-1">{errors.cameraId}</p>
                )}
              </div>

              {/* RTSP URL */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  RTSP URL *
                </label>
                <input
                  type="text"
                  name="rtspUrl"
                  value={formData.rtspUrl}
                  onChange={handleInputChange}
                  placeholder="rtsp://192.168.1.100:554/stream1"
                  className={`input-field ${errors.rtspUrl ? 'border-red-500' : ''}`}
                />
                {errors.rtspUrl && (
                  <p className="text-red-400 text-sm mt-1">{errors.rtspUrl}</p>
                )}
                
                {/* RTSP Examples */}
                <div className="mt-2">
                  <button
                    type="button"
                    onClick={() => setShowExamples(!showExamples)}
                    className="text-blue-400 text-xs hover:text-blue-300 flex items-center"
                  >
                    <Info className="w-3 h-3 mr-1" />
                    {showExamples ? 'Hide' : 'Show'} RTSP URL examples
                  </button>
                  
                  {showExamples && (
                    <div className="mt-2 p-2 bg-gray-800/50 rounded text-xs text-gray-400">
                      <p className="font-medium mb-1">Common RTSP URL formats:</p>
                      {getRTSPExamples().map((example, index) => (
                        <div key={index} className="mb-1">
                          <button
                            type="button"
                            onClick={() => setFormData(prev => ({ ...prev, rtspUrl: example }))}
                            className="text-blue-400 hover:text-blue-300 font-mono text-xs"
                          >
                            {example}
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Credentials */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Username
                  </label>
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleInputChange}
                    placeholder="admin"
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Password
                  </label>
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    placeholder="password"
                    className="input-field"
                  />
                </div>
              </div>

              {/* FPS */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Frame Rate (FPS)
                </label>
                <input
                  type="number"
                  name="fps"
                  value={formData.fps}
                  onChange={handleInputChange}
                  min="1"
                  max="60"
                  className={`input-field ${errors.fps ? 'border-red-500' : ''}`}
                />
                {errors.fps && (
                  <p className="text-red-400 text-sm mt-1">{errors.fps}</p>
                )}
              </div>

              {/* Test Connection */}
              <div>
                <button
                  type="button"
                  onClick={handleTestConnection}
                  disabled={isTestingConnection || !formData.rtspUrl}
                  className="btn-secondary w-full py-3 flex items-center justify-center disabled:opacity-50"
                >
                  {isTestingConnection ? (
                    <Loader className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <TestTube className="w-4 h-4 mr-2" />
                  )}
                  {isTestingConnection ? 'Testing Connection...' : 'Test Connection'}
                </button>
                
                {connectionTestResult && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`mt-3 p-3 rounded-lg flex items-center space-x-2 ${
                      connectionTestResult.success 
                        ? 'bg-green-900/50 text-green-300' 
                        : 'bg-red-900/50 text-red-300'
                    }`}
                  >
                    {connectionTestResult.success ? (
                      <CheckCircle className="w-4 h-4" />
                    ) : (
                      <AlertCircle className="w-4 h-4" />
                    )}
                    <span className="text-sm">{connectionTestResult.message}</span>
                  </motion.div>
                )}
              </div>

              {/* Submit Error */}
              {errors.submit && (
                <div className="bg-red-900/50 text-red-300 p-3 rounded-lg flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4" />
                  <span className="text-sm">{errors.submit}</span>
                </div>
              )}

              {/* Actions */}
              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={handleClose}
                  className="btn-secondary flex-1 py-3"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary flex-1 py-3"
                >
                  Add Camera
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default AddCameraModal;