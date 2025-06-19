import { toast } from 'react-hot-toast';

export const useNotifications = () => {
  const showSuccess = (message, options = {}) => {
    return toast.success(message, {
      ...options,
    });
  };

  const showError = (message, options = {}) => {
    return toast.error(message, {
      ...options,
    });
  };

  const showLoading = (message, options = {}) => {
    return toast.loading(message, {
      ...options,
    });
  };

  const showInfo = (message, options = {}) => {
    return toast(message, {
      icon: 'ℹ️',
      style: {
        border: '1px solid rgba(59, 130, 246, 0.3)',
        background: 'rgba(30, 64, 175, 0.1)',
      },
      ...options,
    });
  };

  const showWarning = (message, options = {}) => {
    return toast(message, {
      icon: '⚠️',
      style: {
        border: '1px solid rgba(245, 158, 11, 0.3)',
        background: 'rgba(180, 83, 9, 0.1)',
      },
      ...options,
    });
  };

  // Helper for promises - shows loading, then success/error
  const promise = (promiseFunction, messages) => {
    return toast.promise(
      promiseFunction,
      {
        loading: messages.loading || 'Loading...',
        success: messages.success || 'Success!',
        error: messages.error || 'Something went wrong',
      }
    );
  };

  // Update an existing toast (useful for loading states)
  const update = (toastId, message, type = 'success') => {
    if (type === 'success') {
      return toast.success(message, { id: toastId });
    } else if (type === 'error') {
      return toast.error(message, { id: toastId });
    } else {
      return toast(message, { id: toastId });
    }
  };

  // Dismiss a specific toast
  const dismiss = (toastId) => {
    return toast.dismiss(toastId);
  };

  // Dismiss all toasts
  const dismissAll = () => {
    return toast.dismiss();
  };

  // Specialized notifications for common operations
  const operations = {
    // Camera operations
    cameraAdded: (cameraId) => showSuccess(`Camera ${cameraId} added successfully`),
    cameraRemoved: (cameraId) => showSuccess(`Camera ${cameraId} removed successfully`),
    cameraTestSuccess: (cameraId) => showSuccess(`Camera ${cameraId} connection test successful`),
    cameraTestFailed: (cameraId, error) => showError(`Camera ${cameraId} connection failed: ${error}`),
    cameraDiscovered: (count) => showInfo(`Found ${count} camera(s) on network`),
    
    // Threshold operations
    thresholdUpdated: (name, value) => showSuccess(`${name} threshold updated to ${value}%`),
    thresholdFailed: (name, error) => showError(`Failed to update ${name} threshold: ${error}`),
    
    // Alert operations
    alertAcknowledged: () => showSuccess('Alert acknowledged'),
    alertsCleared: (count) => showSuccess(`${count} alert(s) cleared`),
    
    // System operations
    systemConnected: () => showSuccess('Connected to detection system'),
    systemDisconnected: () => showWarning('Disconnected from detection system'),
    systemError: (error) => showError(`System error: ${error}`),
    
    // General operations
    saveSuccess: () => showSuccess('Settings saved successfully'),
    saveError: (error) => showError(`Failed to save settings: ${error}`),
    validationError: (message) => showError(`Validation error: ${message}`),
  };

  return {
    showSuccess,
    showError,
    showLoading,
    showInfo,
    showWarning,
    promise,
    update,
    dismiss,
    dismissAll,
    operations,
  };
};

export default useNotifications;