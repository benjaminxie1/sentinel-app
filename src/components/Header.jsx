import React, { useState, useEffect } from 'react';

const Header = ({ systemStatus, alertCount }) => {
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

  return (
    <header className="h-16 bg-gradient-to-r from-command-900 via-command-800 to-safety-900 border-b border-fire-500/30 flex items-center justify-between px-6">
      <div className="flex items-center space-x-4">
        <div className="w-8 h-8 fire-gradient rounded-lg flex items-center justify-center animate-slow-pulse">
          <div className="w-4 h-4 bg-white rounded-sm"></div>
        </div>
        <div>
          <h1 className="text-xl font-bold font-display text-white">SENTINEL</h1>
          <p className="text-xs text-fire-300 font-command">FIRE COMMAND CENTER</p>
        </div>
      </div>
      
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 status-online rounded-full"></div>
          <span className="text-sm font-command text-emerald-400">SYSTEM ONLINE</span>
        </div>
        <div className="text-right">
          <div className="text-sm font-command text-white">{timeString}</div>
          <div className="text-xs text-gray-400">LOCAL TIME</div>
        </div>
      </div>
    </header>
  );
};

export default React.memo(Header);