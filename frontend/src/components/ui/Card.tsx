'use client';

import React from 'react';
import { cn } from '@/lib/utils';

export interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'elevated' | 'glass' | 'gradient';
  hover?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  onClick?: () => void;
}

const variants = {
  default: 'bg-slate-800/50 border border-slate-700/50',
  elevated: 'bg-slate-800 shadow-xl shadow-black/20',
  glass: 'bg-slate-800/30 backdrop-blur-xl border border-slate-700/30',
  gradient: 'bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700/50',
};

const paddings = {
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
  const Component = onClick ? 'button' : 'div';

  return (
    <Component
      className={cn(
        'rounded-2xl transition-all duration-300',
        variants[variant],
        paddings[padding],
        hover && 'hover:shadow-xl hover:shadow-primary-500/10 hover:border-primary-500/30 hover:-translate-y-1',
        onClick && 'cursor-pointer text-left w-full',
        className
      )}
      onClick={onClick}
    >
      {children}
    </Component>
  );
};

export const CardHeader: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className,
}) => <div className={cn('mb-4', className)}>{children}</div>;

export const CardTitle: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className,
}) => <h3 className={cn('text-lg font-semibold text-white', className)}>{children}</h3>;

export const CardDescription: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className,
}) => <p className={cn('text-sm text-slate-400 mt-1', className)}>{children}</p>;
