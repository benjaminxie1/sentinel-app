import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Save, RefreshCw, Check, AlertTriangle, Settings, Info } from 'lucide-react';
import { useTauriCommand } from '../../hooks/useTauriApi';
import { useNotifications } from '../../hooks/useNotifications';
import { validateThreshold, validateThresholdRanges } from '../../utils/validation';

const ThresholdSlider = ({ label, id, value, colorScheme, onChange, isUpdating, validationError }) => {
  const [localValue, setLocalValue] = useState(value);
  const [hasChanges, setHasChanges] = useState(false);
  
  useEffect(() => {
    setLocalValue(value);
    setHasChanges(false);
  }, [value]);

  const handleLocalChange = (newValue) => {
    setLocalValue(newValue);
    setHasChanges(newValue !== value);
  };

  const handleCommit = () => {
    if (localValue !== value) {
      // Validate individual threshold
      const validation = validateThreshold(localValue, 50, 100);
      if (!validation.isValid) {
        return; // Don't commit invalid values
      }
      onChange(id, localValue);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <label className={`text-sm font-semibold text-${colorScheme}-400 uppercase tracking-wider`}>
          {label}
        </label>
        <div className="flex items-center space-x-2">
          <span className="text-xl font-command text-white">{localValue}%</span>
          {isUpdating && <RefreshCw className="w-4 h-4 text-gray-400 animate-spin" />}
          {localValue !== value && (
            <button
              onClick={handleCommit}
              className="p-1 rounded hover:bg-gray-700 transition-colors"
              title="Apply changes"
            >
              <Check className="w-4 h-4 text-success-400" />
            </button>
          )}
        </div>
      </div>
      <div className="relative">
        <input 
          type="range" 
          min="50" 
          max="100" 
          value={localValue}
          onChange={(e) => handleLocalChange(parseInt(e.target.value))}
          onMouseUp={handleCommit}
          onTouchEnd={handleCommit}
          className="w-full h-2 bg-command-700 rounded-lg appearance-none cursor-pointer"
          disabled={isUpdating}
        />
        <div 
          className={`absolute top-0 left-0 h-2 bg-gradient-to-r from-${colorScheme}-600 to-${colorScheme}-400 rounded-lg transition-all`}
          style={{ width: `${(localValue - 50) / 50 * 100}%` }}
        ></div>
      </div>
      <div className="text-xs mt-1">
        {validationError ? (
          <span className="text-error-400 flex items-center">
            <AlertTriangle className="w-3 h-3 mr-1" />
            {validationError}
          </span>
        ) : (
          <span className="text-gray-500">
            Adjust sensitivity for {label.toLowerCase()} • {localValue < 70 ? 'High sensitivity' : localValue < 85 ? 'Medium sensitivity' : 'Low sensitivity'}
          </span>
        )}
      </div>
    </div>
  );
};

const ToggleSetting = ({ label, description, checked, onChange, disabled }) => (
  <label className={`flex items-center justify-between p-3 rounded-lg border border-gray-700 hover:border-gray-600 transition-colors ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}>
    <div>
      <span className="text-gray-300 font-medium">{label}</span>
      {description && <p className="text-xs text-gray-500 mt-1">{description}</p>}
    </div>
    <input 
      type="checkbox" 
      checked={checked}
      onChange={(e) => !disabled && onChange(e.target.checked)}
      disabled={disabled}
      className="w-5 h-5 text-fire-500 bg-command-700 border-command-600 rounded focus:ring-fire-500"
    />
  </label>
);

const DetectionSettingsReal = () => {
  const [thresholds, setThresholds] = useState({
    immediate_alert: 95,  // Default: 95%
    review_queue: 85,     // Default: 85%
    log_only: 70          // Default: 70%
  });

  const [settings, setSettings] = useState({});
  const [updatingThresholds, setUpdatingThresholds] = useState({});
  const [lastSaved, setLastSaved] = useState(null);
  const [validationErrors, setValidationErrors] = useState({});

  // Hooks
  const notifications = useNotifications();
  
  // Tauri commands
  const { execute: getDashboardData } = useTauriCommand('get_dashboard_data');
  const { execute: updateThreshold } = useTauriCommand('update_threshold');

  // Load current configuration from backend
  const loadConfiguration = useCallback(async () => {
    try {
      const data = await getDashboardData();
      
      if (data && data.config) {
        // Extract threshold values from config
        if (data.config.detection_thresholds) {
          const newThresholds = {
            immediate_alert: data.config.detection_thresholds.immediate_alert ? Math.round(data.config.detection_thresholds.immediate_alert * 100) : 95,
            review_queue: data.config.detection_thresholds.review_queue ? Math.round(data.config.detection_thresholds.review_queue * 100) : 85,
            log_only: data.config.detection_thresholds.log_only ? Math.round(data.config.detection_thresholds.log_only * 100) : 70
          };
          setThresholds(newThresholds);
        }
        
        // Extract other settings if available
        if (data.config.settings) {
          setSettings(prev => ({
            ...prev,
            ...data.config.settings
          }));
        }
      }
    } catch (error) {
      console.error('Failed to load configuration:', error);
    }
  }, [getDashboardData]);

  // Handle threshold changes
  const handleThresholdChange = async (id, value) => {
    try {
      setUpdatingThresholds(prev => ({ ...prev, [id]: true }));
      
      // Clear any existing validation errors for this field
      setValidationErrors(prev => ({ ...prev, [id]: null }));
      
      // Validate the individual threshold first
      const individualValidation = validateThreshold(value, 50, 100);
      if (!individualValidation.isValid) {
        setValidationErrors(prev => ({ ...prev, [id]: individualValidation.error }));
        notifications.operations.validationError(individualValidation.error);
        return;
      }
      
      // Create updated thresholds object for range validation
      const updatedThresholds = { ...thresholds, [id]: value };
      
      // Validate threshold ranges
      const rangeValidation = validateThresholdRanges(updatedThresholds);
      if (!rangeValidation.isValid) {
        setValidationErrors(prev => ({ ...prev, [rangeValidation.field]: rangeValidation.error }));
        notifications.operations.validationError(rangeValidation.error);
        return;
      }
      
      // Convert percentage to decimal for backend
      const decimalValue = value / 100;
      
      // Show loading toast
      const loadingToast = notifications.showLoading(`Updating ${id.replace('_', ' ')} threshold...`);
      
      const success = await updateThreshold({ threshold_name: id, value: decimalValue });
      
      // Dismiss loading toast
      notifications.dismiss(loadingToast);
      
      if (success) {
        setThresholds(prev => ({ ...prev, [id]: value }));
        setLastSaved(new Date());
        
        // Clear any validation errors
        setValidationErrors({});
        
        // Show success notification
        notifications.operations.thresholdUpdated(id.replace('_', ' '), value);
      } else {
        notifications.operations.thresholdFailed(id.replace('_', ' '), 'Backend operation failed');
      }
    } catch (error) {
      console.error(`Failed to update threshold ${id}:`, error);
      notifications.operations.thresholdFailed(id.replace('_', ' '), error.message || 'Unknown error');
    } finally {
      setUpdatingThresholds(prev => ({ ...prev, [id]: false }));
    }
  };


  // Load configuration on mount
  useEffect(() => {
    loadConfiguration();
  }, [loadConfiguration]);

  const thresholdConfigs = [
    { 
      label: 'P1 - IMMEDIATE ALERT', 
      id: 'immediate_alert', 
      value: thresholds.immediate_alert, 
      colorScheme: 'emergency',
      description: 'Highest priority alerts requiring immediate response'
    },
    { 
      label: 'P2 - REVIEW QUEUE', 
      id: 'review_queue', 
      value: thresholds.review_queue, 
      colorScheme: 'warning',
      description: 'Medium priority alerts for human verification'
    },
    { 
      label: 'P4 - LOG ONLY', 
      id: 'log_only', 
      value: thresholds.log_only, 
      colorScheme: 'safety',
      description: 'Low priority detections for data collection'
    }
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-8 space-y-8 overflow-y-auto h-full"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold gradient-text mb-2">Detection Settings</h1>
          <p className="text-gray-400">Configure fire detection parameters and thresholds</p>
        </div>
        
        <div className="flex items-center space-x-3">
          {lastSaved && (
            <div className="text-sm text-gray-400">
              Last saved: {lastSaved.toLocaleTimeString()}
            </div>
          )}
          <button
            onClick={loadConfiguration}
            className="btn-ghost text-sm py-2 px-4 flex items-center"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Validation Summary */}
      {Object.keys(validationErrors).some(key => validationErrors[key]) && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="p-4 rounded-lg border bg-warning-900/20 border-warning-500 text-warning-400"
        >
          <div className="flex items-center mb-2">
            <Info className="w-5 h-5 mr-2" />
            <span className="font-semibold">Validation Issues</span>
          </div>
          <div className="text-sm space-y-1">
            <p>Please correct the threshold values to ensure proper detection hierarchy:</p>
            <p className="font-mono text-xs">P1 (Immediate) &gt; P2 (Review) &gt; P4 (Log Only)</p>
          </div>
        </motion.div>
      )}
      
      {/* Confidence Thresholds */}
      <div className="glass rounded-xl p-6">
        <div className="flex items-center mb-6">
          <Settings className="w-6 h-6 text-fire-400 mr-3" />
          <div>
            <h3 className="text-xl font-semibold text-white">Fire Detection Thresholds</h3>
            <p className="text-sm text-gray-400">Adjust confidence levels for different alert priorities</p>
          </div>
        </div>
        
        <div className="space-y-8">
          {thresholdConfigs.map((config, index) => (
            <motion.div
              key={config.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="p-4 rounded-lg border border-gray-700"
            >
              <div className="mb-2">
                <h4 className="font-semibold text-gray-200">{config.label}</h4>
                <p className="text-xs text-gray-500">{config.description}</p>
              </div>
              <ThresholdSlider 
                {...config}
                onChange={handleThresholdChange}
                isUpdating={updatingThresholds[config.id]}
                validationError={validationErrors[config.id]}
              />
            </motion.div>
          ))}
        </div>
        
        <div className="mt-6 p-4 bg-gray-800/50 rounded-lg">
          <h4 className="text-sm font-semibold text-gray-300 mb-2">Threshold Guidelines</h4>
          <div className="text-xs text-gray-500 space-y-1">
            <div>• <strong>P1 (95%+):</strong> Only the most confident detections trigger immediate alerts</div>
            <div>• <strong>P2 (85%+):</strong> Medium confidence detections requiring human review</div>
            <div>• <strong>P4 (70%+):</strong> Low confidence detections logged for analysis</div>
          </div>
        </div>
      </div>
      
    </motion.div>
  );
};

export default React.memo(DetectionSettingsReal);