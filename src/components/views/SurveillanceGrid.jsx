import React from 'react';

const CameraFeed = ({ id, location, status, statusText }) => {
  const statusColor = status === 'online' ? 'emerald' : 'gray';
  
  return (
    <div className="command-panel rounded-xl overflow-hidden">
      <div className="bg-command-700 p-4 border-b border-command-600">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-white font-command">{id}</h3>
            <p className="text-sm text-gray-400">{location}</p>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 bg-${statusColor}-500 rounded-full animate-slow-pulse`}></div>
            <span className={`text-xs font-command text-${statusColor}-400 uppercase`}>
              {status}
            </span>
          </div>
        </div>
      </div>
      <div className="bg-black h-48 flex items-center justify-center relative">
        <div className="text-center">
          <div className="w-16 h-16 bg-command-700 rounded-lg mx-auto mb-3 flex items-center justify-center">
            <div className="w-8 h-8 bg-command-600 rounded"></div>
          </div>
          <p className="text-gray-400 text-sm">{statusText}</p>
        </div>
        {status === 'online' && (
          <div className="absolute top-2 right-2 bg-emerald-500 text-white text-xs px-2 py-1 rounded font-command">
            LIVE
          </div>
        )}
      </div>
    </div>
  );
};

const SurveillanceGrid = () => {
  const cameras = [
    { id: 'CAM_001', location: 'OUTDOOR PERIMETER', status: 'online', statusText: 'No threats detected' },
    { id: 'CAM_002', location: 'INDOOR FACILITY', status: 'online', statusText: 'Clear visibility' },
    { id: 'CAM_003', location: 'SYNTHETIC FEED', status: 'online', statusText: 'Simulation active' },
    { id: 'CAM_004', location: 'BACKUP UNIT', status: 'offline', statusText: 'Maintenance mode' }
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">SURVEILLANCE GRID</h2>
        <p className="text-gray-400">Real-time monitoring of all camera feeds</p>
      </div>
      
      <div className="grid grid-cols-2 gap-6">
        {cameras.map((camera) => (
          <CameraFeed key={camera.id} {...camera} />
        ))}
      </div>
    </div>
  );
};

export default React.memo(SurveillanceGrid);