import React from 'react';
import { cn } from './utils/cn';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Label text */
  label?: string;
  /** Error message */
  error?: string;
  /** Hint text shown below input */
  hint?: string;
  /** Icon shown on the left side */
  iconLeft?: React.ReactNode;
  /** Icon shown on the right side */
  iconRight?: React.ReactNode;
  /** Full width input */
  fullWidth?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      label,
      error,
      hint,
      iconLeft,
      iconRight,
      fullWidth = true,
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || `input-${React.useId()}`;
    const errorId = error ? `${inputId}-error` : undefined;
    const hintId = hint ? `${inputId}-hint` : undefined;

    return (
      <div className={cn('space-y-1.5', fullWidth && 'w-full')}>
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-slate-300"
          >
            {label}
          </label>
        )}
        
        <div className="relative">
          {iconLeft && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
              {iconLeft}
            </div>
          )}
          
          <input
            ref={ref}
            id={inputId}
            className={cn(
              // Base styles
              'w-full px-4 py-3 rounded-xl',
              'bg-slate-800/50 border border-slate-700',
              'text-slate-100 placeholder:text-slate-500',
              'transition-all duration-200',
              // Focus styles
              'focus:outline-none focus:ring-2 focus:ring-indigo-500/50',
              'focus:border-indigo-500',
              // Disabled styles
              'disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-slate-800',
              // Error styles
              error && 'border-red-500 focus:ring-red-500/50 focus:border-red-500',
              // Icon padding
              iconLeft && 'pl-10',
              iconRight && 'pr-10',
              className
            )}
            aria-invalid={error ? 'true' : undefined}
            aria-describedby={
              [errorId, hintId].filter(Boolean).join(' ') || undefined
            }
            {...props}
          />
          
          {iconRight && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
              {iconRight}
            </div>
          )}
        </div>
        
        {error && (
          <p id={errorId} className="text-sm text-red-400" role="alert">
            {error}
          </p>
        )}
        
        {hint && !error && (
          <p id={hintId} className="text-sm text-slate-500">
            {hint}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
