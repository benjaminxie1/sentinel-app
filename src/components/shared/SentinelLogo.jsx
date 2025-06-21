import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';

const SentinelLogo = ({ 
  size = 'medium', 
  animated = true, 
  showText = true, 
  className = '',
  ...props 
}) => {
  const sizeClasses = {
    small: 'w-8 h-8',
    medium: 'w-10 h-10',
    large: 'w-16 h-16',
    xl: 'w-20 h-20'
  };

  const innerSizeClasses = {
    small: 'inset-1.5',
    medium: 'inset-2',
    large: 'inset-3',
    xl: 'inset-4'
  };

  const roundingClasses = {
    small: 'rounded-md',
    medium: 'rounded-lg',
    large: 'rounded-xl',
    xl: 'rounded-2xl'
  };

  const innerRoundingClasses = {
    small: 'rounded-sm',
    medium: 'rounded-sm',
    large: 'rounded-md',
    xl: 'rounded-lg'
  };

  const LogoIcon = ({ className: iconClassName }) => (
    <div
      className={clsx(
        'relative overflow-hidden shadow-lg',
        sizeClasses[size],
        roundingClasses[size],
        iconClassName
      )}
      style={{
        background: 'linear-gradient(135deg, #ef4444 0%, #f59e0b 50%, #fbbf24 100%)',
      }}
      {...props}
    >
      {/* Inner white square */}
      <div
        className={clsx(
          'absolute bg-white',
          innerSizeClasses[size],
          innerRoundingClasses[size]
        )}
      />
      
      {/* Optional glow effect */}
      {animated && (
        <div 
          className="absolute inset-0 opacity-20"
          style={{
            background: 'linear-gradient(135deg, #ef4444 0%, #f59e0b 50%, #fbbf24 100%)',
            filter: 'blur(8px)',
            transform: 'scale(1.2)',
          }}
        />
      )}
    </div>
  );

  if (!showText) {
    return animated ? (
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className={className}
      >
        <LogoIcon className={animated ? 'glow-subtle' : ''} />
      </motion.div>
    ) : (
      <LogoIcon className={className} />
    );
  }

  const textSizeClasses = {
    small: 'text-lg',
    medium: 'text-xl',
    large: 'text-2xl',
    xl: 'text-3xl'
  };

  const Component = animated ? motion.div : 'div';
  const motionProps = animated ? {
    initial: { opacity: 0, y: -10 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6, ease: 'easeOut' }
  } : {};

  return (
    <Component
      className={clsx('flex items-center space-x-3', className)}
      {...motionProps}
    >
      <LogoIcon className={animated ? 'glow-subtle' : ''} />
      
      {showText && (
        <div className="flex flex-col">
          <span 
            className={clsx(
              'font-bold tracking-tight gradient-text font-display',
              textSizeClasses[size]
            )}
          >
            SENTINEL
          </span>
          {(size === 'large' || size === 'xl') && (
            <span className="text-xs text-gray-400 font-medium tracking-wider uppercase">
              Fire Command Center
            </span>
          )}
        </div>
      )}
    </Component>
  );
};

export default SentinelLogo;