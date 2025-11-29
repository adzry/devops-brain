import React from 'react';
import { cn } from '../utils/cn';

export interface SpinnerProps {
  /** Spinner size */
  size?: 'sm' | 'md' | 'lg' | 'xl';
  /** Color variant */
  variant?: 'default' | 'primary' | 'white';
  /** Additional classes */
  className?: string;
  /** Accessible label */
  label?: string;
}

const sizeStyles = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
  xl: 'w-12 h-12',
};

const colorStyles = {
  default: 'text-slate-400',
  primary: 'text-primary-500',
  white: 'text-white',
};

export const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  variant = 'primary',
  className,
  label = 'Loading...',
}) => {
  return (
    <div
      className={cn('inline-flex items-center justify-center', className)}
      role="status"
      aria-label={label}
    >
      <svg
        className={cn(
          'animate-spin',
          sizeStyles[size],
          colorStyles[variant]
        )}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      <span className="sr-only">{label}</span>
    </div>
  );
};

// Alternative spinner with dots
export const DotsSpinner: React.FC<SpinnerProps> = ({
  size = 'md',
  variant = 'primary',
  className,
  label = 'Loading...',
}) => {
  const dotSizes = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-2.5 h-2.5',
    xl: 'w-3 h-3',
  };

  return (
    <div
      className={cn('inline-flex items-center gap-1', className)}
      role="status"
      aria-label={label}
    >
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className={cn(
            'rounded-full',
            dotSizes[size],
            colorStyles[variant],
            'bg-current animate-bounce'
          )}
          style={{
            animationDelay: `${i * 0.15}s`,
            animationDuration: '0.6s',
          }}
        />
      ))}
      <span className="sr-only">{label}</span>
    </div>
  );
};

// Pulse spinner
export const PulseSpinner: React.FC<SpinnerProps> = ({
  size = 'md',
  variant = 'primary',
  className,
  label = 'Loading...',
}) => {
  return (
    <div
      className={cn('relative inline-flex', className)}
      role="status"
      aria-label={label}
    >
      <div
        className={cn(
          'absolute inset-0 rounded-full animate-ping opacity-75',
          sizeStyles[size],
          variant === 'primary' ? 'bg-primary-500' : 
          variant === 'white' ? 'bg-white' : 'bg-slate-400'
        )}
      />
      <div
        className={cn(
          'relative rounded-full',
          sizeStyles[size],
          variant === 'primary' ? 'bg-primary-500' : 
          variant === 'white' ? 'bg-white' : 'bg-slate-400'
        )}
      />
      <span className="sr-only">{label}</span>
    </div>
  );
};
