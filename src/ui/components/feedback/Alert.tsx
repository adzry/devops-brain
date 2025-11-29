import React from 'react';
import { cn } from '../utils/cn';

export interface AlertProps {
  /** Alert title */
  title?: string;
  /** Alert message */
  children: React.ReactNode;
  /** Alert variant */
  variant?: 'info' | 'success' | 'warning' | 'error';
  /** Show icon */
  showIcon?: boolean;
  /** Dismissible alert */
  dismissible?: boolean;
  /** On dismiss callback */
  onDismiss?: () => void;
  /** Additional classes */
  className?: string;
}

const variantStyles = {
  info: {
    container: 'bg-blue-500/10 border-blue-500/30 text-blue-200',
    icon: 'text-blue-400',
  },
  success: {
    container: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-200',
    icon: 'text-emerald-400',
  },
  warning: {
    container: 'bg-amber-500/10 border-amber-500/30 text-amber-200',
    icon: 'text-amber-400',
  },
  error: {
    container: 'bg-red-500/10 border-red-500/30 text-red-200',
    icon: 'text-red-400',
  },
};

const icons = {
  info: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  success: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  warning: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
  error: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
};

export const Alert: React.FC<AlertProps> = ({
  title,
  children,
  variant = 'info',
  showIcon = true,
  dismissible = false,
  onDismiss,
  className,
}) => {
  return (
    <div
      className={cn(
        'relative flex gap-3 p-4 rounded-xl border',
        variantStyles[variant].container,
        className
      )}
      role="alert"
    >
      {showIcon && (
        <div className={cn('flex-shrink-0', variantStyles[variant].icon)}>
          {icons[variant]}
        </div>
      )}
      
      <div className="flex-1 min-w-0">
        {title && (
          <h3 className="font-semibold text-white mb-1">{title}</h3>
        )}
        <div className="text-sm">{children}</div>
      </div>
      
      {dismissible && (
        <button
          onClick={onDismiss}
          className={cn(
            'flex-shrink-0 p-1 -m-1 rounded-lg',
            'text-current opacity-50 hover:opacity-100',
            'transition-opacity',
            'focus:outline-none focus:ring-2 focus:ring-current focus:ring-opacity-50'
          )}
          aria-label="Dismiss"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
};
