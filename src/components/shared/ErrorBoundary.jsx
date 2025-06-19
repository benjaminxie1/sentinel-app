import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null,
      errorInfo: null,
      errorId: null
    };
  }

  static getDerivedStateFromError(error) {
    return { 
      hasError: true,
      errorId: Date.now().toString()
    };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // Log error for fire safety system monitoring
    console.error('🚨 CRITICAL: Fire Detection UI Error:', {
      error: error.toString(),
      errorInfo: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      errorId: this.state.errorId
    });

    // For production, you might want to send this to a logging service
    // that works offline for local fire detection systems
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    });
  };

  render() {
    if (this.state.hasError) {
      const { fallbackComponent: FallbackComponent, title = "Fire Detection System Error" } = this.props;

      // If a custom fallback component is provided, use it
      if (FallbackComponent) {
        return (
          <FallbackComponent
            error={this.state.error}
            errorInfo={this.state.errorInfo}
            onRetry={this.handleRetry}
          />
        );
      }

      // Default error UI for fire detection system
      return (
        <div className="min-h-screen bg-gray-950 text-gray-100 flex items-center justify-center p-6">
          <div className="max-w-md w-full">
            <div className="glass rounded-xl p-8 text-center">
              <div className="w-16 h-16 bg-fire-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <AlertTriangle className="w-8 h-8 text-fire-400" />
              </div>
              
              <h1 className="text-xl font-bold text-fire-400 mb-4">
                {title}
              </h1>
              
              <p className="text-gray-300 mb-6 leading-relaxed">
                A critical error occurred in the fire detection interface. 
                The backend detection system may still be running. 
                Please retry or contact system administrator.
              </p>

              <div className="space-y-4">
                <button
                  onClick={this.handleRetry}
                  className="btn-primary w-full"
                >
                  <RefreshCw className="w-4 h-4" />
                  Retry Interface
                </button>

                {process.env.NODE_ENV === 'development' && (
                  <details className="text-left bg-gray-900/50 rounded-lg p-4 text-xs">
                    <summary className="cursor-pointer text-gray-400 mb-2">
                      Error Details (Development)
                    </summary>
                    <div className="space-y-2">
                      <div>
                        <strong className="text-fire-400">Error ID:</strong> {this.state.errorId}
                      </div>
                      <div>
                        <strong className="text-fire-400">Error:</strong>
                        <pre className="text-gray-300 mt-1 whitespace-pre-wrap">
                          {this.state.error && this.state.error.toString()}
                        </pre>
                      </div>
                      <div>
                        <strong className="text-fire-400">Component Stack:</strong>
                        <pre className="text-gray-300 mt-1 whitespace-pre-wrap">
                          {this.state.errorInfo && this.state.errorInfo.componentStack}
                        </pre>
                      </div>
                    </div>
                  </details>
                )}
              </div>

              <p className="text-xs text-gray-500 mt-6">
                Error ID: {this.state.errorId} | {new Date().toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;