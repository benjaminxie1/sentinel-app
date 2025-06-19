/**
 * Validation utilities for form inputs and data
 */

// Threshold validation
export const validateThreshold = (value, min = 50, max = 100) => {
  const numValue = parseFloat(value);
  
  if (isNaN(numValue)) {
    return { isValid: false, error: 'Value must be a number' };
  }
  
  if (numValue < min || numValue > max) {
    return { isValid: false, error: `Value must be between ${min}% and ${max}%` };
  }
  
  return { isValid: true, error: null };
};

// Threshold range validation (ensures P1 > P2 > P4)
export const validateThresholdRanges = (thresholds) => {
  const { immediate_alert, review_queue, log_only } = thresholds;
  
  if (immediate_alert <= review_queue) {
    return { 
      isValid: false, 
      error: 'P1 (Immediate Alert) threshold must be higher than P2 (Review Queue)',
      field: 'immediate_alert'
    };
  }
  
  if (review_queue <= log_only) {
    return { 
      isValid: false, 
      error: 'P2 (Review Queue) threshold must be higher than P4 (Log Only)',
      field: 'review_queue'
    };
  }
  
  if (immediate_alert - review_queue < 5) {
    return { 
      isValid: false, 
      error: 'P1 and P2 thresholds should have at least 5% difference for clear distinction',
      field: 'immediate_alert'
    };
  }
  
  if (review_queue - log_only < 5) {
    return { 
      isValid: false, 
      error: 'P2 and P4 thresholds should have at least 5% difference for clear distinction',
      field: 'review_queue'
    };
  }
  
  return { isValid: true, error: null, field: null };
};

// RTSP URL validation
export const validateRTSPUrl = (url) => {
  if (!url || url.trim() === '') {
    return { isValid: false, error: 'RTSP URL is required' };
  }
  
  // Basic RTSP URL pattern
  const rtspPattern = /^rtsp:\/\/(?:[\w\.\-]+(?::[\w\.\-]+)?@)?[\w\.\-]+(?::\d{1,5})?(?:\/[\w\.\-\/\?&=]*)?$/i;
  
  if (!rtspPattern.test(url.trim())) {
    return { 
      isValid: false, 
      error: 'Invalid RTSP URL format. Example: rtsp://username:password@192.168.1.100:554/stream' 
    };
  }
  
  return { isValid: true, error: null };
};

// Camera ID validation
export const validateCameraId = (id, existingIds = []) => {
  if (!id || id.trim() === '') {
    return { isValid: false, error: 'Camera ID is required' };
  }
  
  // Check for valid characters (alphanumeric, underscore, hyphen)
  const idPattern = /^[a-zA-Z0-9_-]+$/;
  if (!idPattern.test(id.trim())) {
    return { 
      isValid: false, 
      error: 'Camera ID can only contain letters, numbers, underscores, and hyphens' 
    };
  }
  
  // Check length
  if (id.trim().length < 3 || id.trim().length > 20) {
    return { isValid: false, error: 'Camera ID must be between 3 and 20 characters' };
  }
  
  // Check for duplicates
  if (existingIds.includes(id.trim().toUpperCase())) {
    return { isValid: false, error: 'Camera ID already exists' };
  }
  
  return { isValid: true, error: null };
};

// IP address validation
export const validateIPAddress = (ip) => {
  if (!ip || ip.trim() === '') {
    return { isValid: false, error: 'IP address is required' };
  }
  
  const ipPattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
  
  if (!ipPattern.test(ip.trim())) {
    return { isValid: false, error: 'Invalid IP address format (e.g., 192.168.1.100)' };
  }
  
  return { isValid: true, error: null };
};

// Port validation
export const validatePort = (port) => {
  if (!port) {
    return { isValid: true, error: null }; // Port is optional
  }
  
  const numPort = parseInt(port);
  
  if (isNaN(numPort)) {
    return { isValid: false, error: 'Port must be a number' };
  }
  
  if (numPort < 1 || numPort > 65535) {
    return { isValid: false, error: 'Port must be between 1 and 65535' };
  }
  
  return { isValid: true, error: null };
};

// Username validation
export const validateUsername = (username) => {
  if (!username) {
    return { isValid: true, error: null }; // Username is optional
  }
  
  if (username.length < 2 || username.length > 50) {
    return { isValid: false, error: 'Username must be between 2 and 50 characters' };
  }
  
  return { isValid: true, error: null };
};

// Password validation
export const validatePassword = (password) => {
  if (!password) {
    return { isValid: true, error: null }; // Password is optional
  }
  
  if (password.length < 3 || password.length > 100) {
    return { isValid: false, error: 'Password must be between 3 and 100 characters' };
  }
  
  return { isValid: true, error: null };
};

// Comprehensive form validation
export const validateCameraForm = (formData, existingCameraIds = []) => {
  const errors = {};
  
  // Validate camera ID
  const idValidation = validateCameraId(formData.cameraId, existingCameraIds);
  if (!idValidation.isValid) {
    errors.cameraId = idValidation.error;
  }
  
  // Validate RTSP URL
  const urlValidation = validateRTSPUrl(formData.rtspUrl);
  if (!urlValidation.isValid) {
    errors.rtspUrl = urlValidation.error;
  }
  
  // Validate username if provided
  const usernameValidation = validateUsername(formData.username);
  if (!usernameValidation.isValid) {
    errors.username = usernameValidation.error;
  }
  
  // Validate password if provided
  const passwordValidation = validatePassword(formData.password);
  if (!passwordValidation.isValid) {
    errors.password = passwordValidation.error;
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

// Helper function to get RTSP URL examples
export const getRTSPExamples = () => [
  'rtsp://192.168.1.100:554/stream',
  'rtsp://username:password@192.168.1.100:554/live',
  'rtsp://admin:admin123@10.0.0.50/h264',
  'rtsp://192.168.1.200:8554/live.sdp'
];

// Helper function to get common validation messages
export const getValidationMessages = () => ({
  required: 'This field is required',
  invalidFormat: 'Invalid format',
  tooShort: 'Value is too short',
  tooLong: 'Value is too long',
  outOfRange: 'Value is out of range',
  duplicate: 'Value already exists',
  invalidCharacters: 'Contains invalid characters'
});

export default {
  validateThreshold,
  validateThresholdRanges,
  validateRTSPUrl,
  validateCameraId,
  validateIPAddress,
  validatePort,
  validateUsername,
  validatePassword,
  validateCameraForm,
  getRTSPExamples,
  getValidationMessages
};