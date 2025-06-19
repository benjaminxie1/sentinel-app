import { useState, useEffect, useCallback } from 'react';

// Tauri API wrapper
let tauriApi = null;

// Initialize Tauri API
const initTauriApi = async () => {
  if (tauriApi) return tauriApi;
  
  try {
    // Check if we're in Tauri environment
    if (window.__TAURI__) {
      const { invoke } = await import('@tauri-apps/api/core');
      const { listen } = await import('@tauri-apps/api/event');
      
      tauriApi = {
        invoke,
        listen,
        isAvailable: true
      };
    } else {
      // Fallback for development mode
      tauriApi = {
        invoke: async (command, args) => {
          console.warn(`Tauri command ${command} called in development mode`);
          return null;
        },
        listen: (event, callback) => {
          console.warn(`Tauri event ${event} listener registered in development mode`);
          return () => {};
        },
        isAvailable: false
      };
    }
  } catch (error) {
    console.error('Failed to initialize Tauri API:', error);
    tauriApi = {
      invoke: async () => null,
      listen: () => () => {},
      isAvailable: false
    };
  }
  
  return tauriApi;
};

export const useTauriApi = () => {
  const [api, setApi] = useState(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    initTauriApi().then((tauriInstance) => {
      setApi(tauriInstance);
      setIsReady(true);
    });
  }, []);

  return { api, isReady };
};

export const useTauriCommand = (command, initialArgs = null) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { api, isReady } = useTauriApi();

  const execute = useCallback(async (args = initialArgs) => {
    if (!api || !isReady) return null;

    setLoading(true);
    setError(null);

    try {
      const result = await api.invoke(command, args || {});
      setData(result);
      return result;
    } catch (err) {
      console.error(`Tauri command ${command} failed:`, err);
      setError(err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [api, isReady, command, initialArgs]);

  return { data, loading, error, execute };
};

export const useTauriEvent = (eventName, callback) => {
  const { api, isReady } = useTauriApi();

  useEffect(() => {
    if (!api || !isReady || !callback) return;

    let unlisten;

    const setupListener = async () => {
      try {
        unlisten = await api.listen(eventName, callback);
      } catch (error) {
        console.error(`Failed to listen to event ${eventName}:`, error);
      }
    };

    setupListener();

    return () => {
      if (unlisten) {
        unlisten();
      }
    };
  }, [api, isReady, eventName, callback]);
};