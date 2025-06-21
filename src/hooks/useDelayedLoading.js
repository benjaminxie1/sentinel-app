import { useState, useEffect, useRef } from 'react';

/**
 * Industrial-grade loading state hook that prevents flashing for fast responses
 * Based on UX research: 
 * - <200ms: No loading indicator needed
 * - >200ms: Show indicator for minimum 500ms to prevent flashing
 * - Stale data better than loading spinner in critical systems
 */
export const useDelayedLoading = (
  isLoading, 
  options = {}
) => {
  const {
    delay = 200,           // Don't show loading for first 200ms
    minDuration = 500,     // Keep loading visible for at least 500ms once shown
    enableStaleData = true // Keep previous data visible during revalidation
  } = options;

  const [shouldShowLoading, setShouldShowLoading] = useState(false);
  const [isStale, setIsStale] = useState(false);
  
  const delayTimeoutRef = useRef(null);
  const minDurationTimeoutRef = useRef(null);
  const loadingStartTimeRef = useRef(null);

  useEffect(() => {
    // Clear any existing timeouts
    if (delayTimeoutRef.current) {
      clearTimeout(delayTimeoutRef.current);
      delayTimeoutRef.current = null;
    }

    if (isLoading) {
      // Mark data as stale immediately if we support stale data
      if (enableStaleData) {
        setIsStale(true);
      }

      // Set timeout to show loading after delay
      delayTimeoutRef.current = setTimeout(() => {
        setShouldShowLoading(true);
        loadingStartTimeRef.current = Date.now();
        delayTimeoutRef.current = null;
      }, delay);
    } else {
      // Loading finished
      setIsStale(false);
      
      if (shouldShowLoading) {
        // If we're currently showing loading, ensure minimum duration
        const loadingDuration = Date.now() - (loadingStartTimeRef.current || 0);
        const remainingTime = Math.max(0, minDuration - loadingDuration);
        
        if (remainingTime > 0) {
          minDurationTimeoutRef.current = setTimeout(() => {
            setShouldShowLoading(false);
            minDurationTimeoutRef.current = null;
          }, remainingTime);
        } else {
          setShouldShowLoading(false);
        }
      } else {
        // Loading finished before delay - no need to show spinner
        setShouldShowLoading(false);
      }
    }

    // Cleanup
    return () => {
      if (delayTimeoutRef.current) {
        clearTimeout(delayTimeoutRef.current);
      }
      if (minDurationTimeoutRef.current) {
        clearTimeout(minDurationTimeoutRef.current);
      }
    };
  }, [isLoading, delay, minDuration, shouldShowLoading, enableStaleData]);

  return {
    shouldShowLoading,
    isStale,
    // For debugging in dev
    _debug: {
      isLoading,
      shouldShowLoading,
      isStale
    }
  };
};