import React from 'react';
import { cn } from '../utils/cn';

export interface BadgeProps {
  /** Badge content */
  children: React.ReactNode;
  /** Visual variant */
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  /** Badge size */
  size?: 'sm' | 'md' | 'lg';
  /** Outlined style */
  outlined?: boolean;
  /** Dot indicator */
  dot?: boolean;
  /** Additional classes */
  className?: string;
}

const variantStyles = {
  default: {
    solid: 'bg-slate-700 text-slate-200',
    outlined: 'border-slate-600 text-slate-300',
  },
  primary: {
    solid: 'bg-primary-500/20 text-primary-400',
    outlined: 'border-primary-500/50 text-primary-400',
  },
  secondary: {
    solid: 'bg-secondary-500/20 text-secondary-400',
    outlined: 'border-secondary-500/50 text-secondary-400',
  },
  success: {
    solid: 'bg-emerald-500/20 text-emerald-400',
    outlined: 'border-emerald-500/50 text-emerald-400',
  },
  warning: {
    solid: 'bg-amber-500/20 text-amber-400',
    outlined: 'border-amber-500/50 text-amber-400',
  },
  error: {
    solid: 'bg-red-500/20 text-red-400',
    outlined: 'border-red-500/50 text-red-400',
  },
  info: {
    solid: 'bg-blue-500/20 text-blue-400',
    outlined: 'border-blue-500/50 text-blue-400',
  },
};

const dotColors = {
  default: 'bg-slate-400',
  primary: 'bg-primary-400',
  secondary: 'bg-secondary-400',
  success: 'bg-emerald-400',
  warning: 'bg-amber-400',
  error: 'bg-red-400',
  info: 'bg-blue-400',
};

const sizeStyles = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-xs',
  lg: 'px-3 py-1.5 text-sm',
};

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  outlined = false,
  dot = false,
  className,
}) => {
  const style = outlined ? 'outlined' : 'solid';
  
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 font-medium rounded-full',
        sizeStyles[size],
        variantStyles[variant][style],
        outlined && 'border bg-transparent',
        className
      )}
    >
      {dot && (
        <span
          className={cn(
            'w-1.5 h-1.5 rounded-full',
            dotColors[variant]
          )}
        />
      )}
      {children}
    </span>
  );
};
