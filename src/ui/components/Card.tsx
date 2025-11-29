import React from 'react';
import { cn } from './utils/cn';

export interface CardProps {
  /** Card content */
  children: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
  /** Visual style variant */
  variant?: 'default' | 'elevated' | 'outlined' | 'gradient' | 'glass';
  /** Enable hover effects */
  hover?: boolean;
  /** Padding size */
  padding?: 'none' | 'sm' | 'md' | 'lg';
  /** Click handler - makes card interactive */
  onClick?: () => void;
}

const variantStyles = {
  default: 'bg-slate-800/50 border border-slate-700/50',
  elevated: 'bg-slate-800 shadow-xl shadow-black/20',
  outlined: 'bg-transparent border-2 border-slate-700',
  gradient: 'bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700/50',
  glass: 'bg-slate-800/30 backdrop-blur-xl border border-slate-700/30',
};

const paddingStyles = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

export const Card: React.FC<CardProps> = ({
  children,
  className,
  variant = 'default',
  hover = false,
  padding = 'md',
  onClick,
}) => {
  const isInteractive = hover || onClick;
  const Component = onClick ? 'button' : 'div';

  return (
    <Component
      className={cn(
        // Base styles
        'rounded-2xl',
        'transition-all duration-300',
        // Variant styles
        variantStyles[variant],
        // Padding styles
        paddingStyles[padding],
        // Hover effects
        isInteractive && [
          'hover:shadow-xl hover:shadow-indigo-500/10',
          'hover:border-indigo-500/30',
          'hover:-translate-y-1',
        ],
        // Interactive styles
        onClick && [
          'cursor-pointer',
          'focus:outline-none focus:ring-2 focus:ring-indigo-500/50',
          'focus:ring-offset-2 focus:ring-offset-slate-900',
          'text-left w-full',
        ],
        className
      )}
      onClick={onClick}
      type={onClick ? 'button' : undefined}
    >
      {children}
    </Component>
  );
};

// Card subcomponents for composition
export interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export const CardHeader: React.FC<CardHeaderProps> = ({ children, className }) => (
  <div className={cn('mb-4', className)}>{children}</div>
);

export interface CardTitleProps {
  children: React.ReactNode;
  className?: string;
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
}

export const CardTitle: React.FC<CardTitleProps> = ({
  children,
  className,
  as: Component = 'h3',
}) => (
  <Component className={cn('text-lg font-semibold text-white', className)}>
    {children}
  </Component>
);

export interface CardDescriptionProps {
  children: React.ReactNode;
  className?: string;
}

export const CardDescription: React.FC<CardDescriptionProps> = ({
  children,
  className,
}) => (
  <p className={cn('text-sm text-slate-400 mt-1', className)}>{children}</p>
);

export interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

export const CardContent: React.FC<CardContentProps> = ({ children, className }) => (
  <div className={cn('', className)}>{children}</div>
);

export interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
}

export const CardFooter: React.FC<CardFooterProps> = ({ children, className }) => (
  <div className={cn('mt-4 pt-4 border-t border-slate-700/50', className)}>
    {children}
  </div>
);
