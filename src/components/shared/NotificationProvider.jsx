import React from 'react';
import { Toaster } from 'react-hot-toast';

const NotificationProvider = ({ children }) => {
  return (
    <>
      {children}
      <Toaster
        position="top-right"
        toastOptions={{
          // Default options for all toasts
          duration: 4000,
          style: {
            background: 'rgba(17, 24, 39, 0.95)', // Dark background matching app theme
            color: '#f3f4f6',
            border: '1px solid rgba(75, 85, 99, 0.3)',
            borderRadius: '0.75rem',
            fontSize: '14px',
            fontFamily: '"Inter", system-ui, sans-serif',
            backdropFilter: 'blur(12px)',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3)',
          },
          // Success toasts
          success: {
            duration: 3000,
            style: {
              border: '1px solid rgba(34, 197, 94, 0.3)',
              background: 'rgba(21, 128, 61, 0.1)',
            },
            iconTheme: {
              primary: '#22c55e',
              secondary: '#f3f4f6',
            },
          },
          // Error toasts
          error: {
            duration: 6000,
            style: {
              border: '1px solid rgba(239, 68, 68, 0.3)',
              background: 'rgba(185, 28, 28, 0.1)',
            },
            iconTheme: {
              primary: '#ef4444',
              secondary: '#f3f4f6',
            },
          },
          // Loading toasts
          loading: {
            style: {
              border: '1px solid rgba(59, 130, 246, 0.3)',
              background: 'rgba(30, 64, 175, 0.1)',
            },
            iconTheme: {
              primary: '#3b82f6',
              secondary: '#f3f4f6',
            },
          },
        }}
      />
    </>
  );
};

export default NotificationProvider;