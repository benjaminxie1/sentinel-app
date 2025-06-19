import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Trash2, Check, X, Info } from 'lucide-react';

const ConfirmDialog = ({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title, 
  message, 
  confirmText = 'Confirm', 
  cancelText = 'Cancel',
  type = 'warning', // 'warning', 'danger', 'info'
  isLoading = false 
}) => {
  const getTypeConfig = () => {
    switch (type) {
      case 'danger':
        return {
          icon: Trash2,
          iconBg: 'bg-red-900/50',
          iconColor: 'text-red-400',
          confirmBtn: 'btn-danger',
          borderColor: 'border-red-500/30'
        };
      case 'info':
        return {
          icon: Info,
          iconBg: 'bg-blue-900/50',
          iconColor: 'text-blue-400',
          confirmBtn: 'btn-primary',
          borderColor: 'border-blue-500/30'
        };
      default: // warning
        return {
          icon: AlertTriangle,
          iconBg: 'bg-yellow-900/50',
          iconColor: 'text-yellow-400',
          confirmBtn: 'btn-warning',
          borderColor: 'border-yellow-500/30'
        };
    }
  };

  const config = getTypeConfig();
  const Icon = config.icon;

  const handleConfirm = async () => {
    try {
      await onConfirm();
      onClose();
    } catch (error) {
      // Let the parent handle the error, don't close the dialog
      console.error('Confirmation action failed:', error);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
          />
          
          {/* Dialog */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', duration: 0.3, damping: 25, stiffness: 300 }}
            className={`relative bg-gray-900 rounded-xl p-6 w-full max-w-md mx-4 border ${config.borderColor} shadow-2xl`}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center space-x-3 mb-4">
              <div className={`p-2 rounded-lg ${config.iconBg}`}>
                <Icon className={`w-5 h-5 ${config.iconColor}`} />
              </div>
              <h3 className="text-lg font-semibold text-white">{title}</h3>
            </div>
            
            {/* Message */}
            <p className="text-gray-300 mb-6 leading-relaxed">
              {message}
            </p>
            
            {/* Actions */}
            <div className="flex space-x-3">
              <button
                onClick={onClose}
                disabled={isLoading}
                className="btn-secondary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {cancelText}
              </button>
              <button
                onClick={handleConfirm}
                disabled={isLoading}
                className={`${config.confirmBtn} flex-1 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center`}
              >
                {isLoading ? (
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  confirmText
                )}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

// Pre-configured confirmation dialogs for common actions
export const DeleteConfirmDialog = ({ isOpen, onClose, onConfirm, itemName, isLoading }) => (
  <ConfirmDialog
    isOpen={isOpen}
    onClose={onClose}
    onConfirm={onConfirm}
    title="Delete Item"
    message={`Are you sure you want to delete "${itemName}"? This action cannot be undone.`}
    confirmText="Delete"
    cancelText="Cancel"
    type="danger"
    isLoading={isLoading}
  />
);

export const RemoveCameraConfirmDialog = ({ isOpen, onClose, onConfirm, cameraName, isLoading }) => (
  <ConfirmDialog
    isOpen={isOpen}
    onClose={onClose}
    onConfirm={onConfirm}
    title="Remove Camera"
    message={`Are you sure you want to remove camera "${cameraName}"? This will stop monitoring from this camera and remove it from the system.`}
    confirmText="Remove Camera"
    cancelText="Cancel"
    type="danger"
    isLoading={isLoading}
  />
);

export const ClearAlertsConfirmDialog = ({ isOpen, onClose, onConfirm, alertCount, isLoading }) => (
  <ConfirmDialog
    isOpen={isOpen}
    onClose={onClose}
    onConfirm={onConfirm}
    title="Clear All Alerts"
    message={`Are you sure you want to acknowledge all ${alertCount} alert(s)? This action will mark them as reviewed and remove them from the active alerts list.`}
    confirmText="Clear All Alerts"
    cancelText="Cancel"
    type="warning"
    isLoading={isLoading}
  />
);

export const ThresholdChangeConfirmDialog = ({ isOpen, onClose, onConfirm, thresholdName, oldValue, newValue, isLoading }) => (
  <ConfirmDialog
    isOpen={isOpen}
    onClose={onClose}
    onConfirm={onConfirm}
    title="Update Detection Threshold"
    message={`Update ${thresholdName} threshold from ${oldValue}% to ${newValue}%? This will affect how sensitive the fire detection system is for this alert level.`}
    confirmText="Update Threshold"
    cancelText="Cancel"
    type="info"
    isLoading={isLoading}
  />
);

export default ConfirmDialog;