import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, Shield } from 'lucide-react';
import clsx from 'clsx';
import SentinelLogo from './shared/SentinelLogo';

const Header = ({ systemStatus, alertCount, isRefreshing, isStale }) => {
  const [currentTime, setCurrentTime] = useState(new Date());

  // Optimized clock updates
  useEffect(() => {
    const updateClock = () => {
      setCurrentTime(new Date());
    };

    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  const timeString = currentTime.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });

  const dateString = currentTime.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });

  // Determine system status configuration with better handling
  const getSystemStatusConfig = () => {
    const health = systemStatus?.systemHealth || 'optimal'; // Default to optimal to prevent flashing
    
    // If we're using stale data, show stable state instead of degraded state
    if (isStale && health === 'optimal') {
      return {
        color: 'success',
        text: 'SYSTEM OPTIMAL',
        icon: Shield,
        dotClass: 'bg-success-500',
        textClass: 'text-success-400'
      };
    }
    
    switch (health) {
      case 'optimal':
        return {
          color: 'success',
          text: 'SYSTEM OPTIMAL',
          icon: Shield,
          dotClass: 'bg-success-500',
          textClass: 'text-success-400'
        };
      case 'warning':
        return {
          color: 'warning',
          text: 'SYSTEM WARNING',
          icon: AlertTriangle,
          dotClass: 'bg-warning-500',
          textClass: 'text-warning-400'
        };
      case 'critical':
        return {
          color: 'error',
          text: 'SYSTEM CRITICAL',
          icon: AlertTriangle,
          dotClass: 'bg-error-500 animate-pulse',
          textClass: 'text-error-400'
        };
      case 'starting':
        return {
          color: 'accent',
          text: 'SYSTEM READY',
          icon: Shield,
          dotClass: 'bg-accent-500',
          textClass: 'text-accent-400'
        };
      default:
        return {
          color: 'success', // Default to success instead of gray
          text: 'SYSTEM READY',
          icon: Shield,
          dotClass: 'bg-success-500',
          textClass: 'text-success-400'
        };
    }
  };

  const statusConfig = getSystemStatusConfig();
  const StatusIcon = statusConfig.icon;

  return (
    <motion.header 
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className="h-16 glass-header flex items-center justify-between px-6 relative"
    >
      {/* Logo and Brand */}
      <div className="flex items-center space-x-4">
        <SentinelLogo size="medium" animated={true} showText={true} />
      </div>
      
      {/* Center Status Indicators */}
      <div className="hidden md:flex items-center space-x-6">
        {/* Active Alerts */}
        {alertCount > 0 && (
          <motion.div 
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="flex items-center space-x-2"
          >
            <div className="w-3 h-3 bg-fire-500 rounded-full" />
            <span className="text-sm font-command text-fire-400 font-semibold">
              {alertCount} ACTIVE ALERT{alertCount !== 1 ? 'S' : ''}
            </span>
          </motion.div>
        )}

        {/* Camera Status */}
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-accent-500 rounded-full" />
          <span className="text-sm font-command text-accent-400">
            {systemStatus?.cameras || 0} CAMERAS
          </span>
        </div>
      </div>
      
      {/* Right Side - System Status and Time */}
      <div className="flex items-center space-x-6">
        {/* System Status */}
        <div className="flex items-center space-x-2">
          <StatusIcon className="w-4 h-4 text-gray-400" />
          <div className={clsx('w-3 h-3 rounded-full', statusConfig.dotClass)} />
          <span className={clsx('text-sm font-command font-semibold hidden sm:block', statusConfig.textClass)}>
            {statusConfig.text}
            {isStale && <span className="ml-1 text-xs opacity-60">(CACHED)</span>}
          </span>
          {isRefreshing && (
            <div className="w-2 h-2 bg-accent-500 rounded-full animate-pulse ml-1" title="Refreshing..." />
          )}
        </div>

        {/* Time Display */}
        <div className="text-right">
          <div className="text-sm font-command text-gray-100 font-semibold tracking-wider">
            {timeString}
          </div>
          <div className="text-xs text-gray-400 font-medium">
            {dateString}
          </div>
        </div>
      </div>

      {/* Background glow effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-fire-950/20 via-transparent to-fire-950/20 pointer-events-none" />
    </motion.header>
  );
};

export default React.memo(Header);