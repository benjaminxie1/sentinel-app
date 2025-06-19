import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './components/App';
import ErrorBoundary from './components/shared/ErrorBoundary';
import './styles.css';

// Initialize React application with error boundary for fire safety system
ReactDOM.createRoot(document.getElementById('app')).render(
  <React.StrictMode>
    <ErrorBoundary title="SENTINEL Fire Detection System Error">
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);