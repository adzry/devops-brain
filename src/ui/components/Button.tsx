import React from 'react';
import { cn } from './utils/cn';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual style variant */
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success';
  /** Size of the button */
  size?: 'sm' | 'md' | 'lg';
  /** Show loading spinner */
  loading?: boolean;
  /** Icon to show before children */
  iconLeft?: React.ReactNode;
  /** Icon to show after children */
  iconRight?: React.ReactNode;
  /** Full width button */
  fullWidth?: boolean;
  /** Button content */
  children: React.ReactNode;
}

const variantStyles = {
  primary: `
    bg-gradient-to-r from-indigo-500 to-indigo-600
    hover:from-indigo-600 hover:to-indigo-700
    text-white
    shadow-lg shadow-indigo-500/25
    hover:shadow-xl hover:shadow-indigo-500/30
    focus:ring-indigo-500/50
  `,
  secondary: `
    bg-slate-800 
    border border-slate-700
    hover:bg-slate-700 hover:border-slate-600
    text-slate-100
    focus:ring-slate-500/50
  `,
  ghost: `
    bg-transparent
    hover:bg-slate-800
    text-slate-300 hover:text-white
    focus:ring-slate-500/50
  `,
  danger: `
    bg-gradient-to-r from-red-500 to-rose-600
    hover:from-red-600 hover:to-rose-700
    text-white
    shadow-lg shadow-red-500/25
    hover:shadow-xl hover:shadow-red-500/30
    focus:ring-red-500/50
  `,
  success: `
    bg-gradient-to-r from-emerald-500 to-emerald-600
    hover:from-emerald-600 hover:to-emerald-700
    text-white
    shadow-lg shadow-emerald-500/25
    hover:shadow-xl hover:shadow-emerald-500/30
    focus:ring-emerald-500/50
  `,
};

const sizeStyles = {
  sm: 'px-3 py-1.5 text-sm gap-1.5 rounded-lg',
  md: 'px-5 py-2.5 text-base gap-2 rounded-xl',
  lg: 'px-7 py-3.5 text-lg gap-2.5 rounded-xl',
};

const Spinner = () => (
  <svg
    className="animate-spin h-5 w-5"
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
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
    />
  </svg>
);

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      loading = false,
      iconLeft,
      iconRight,
      fullWidth = false,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        className={cn(
          // Base styles
          'inline-flex items-center justify-center',
          'font-semibold',
          'transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900',
          'disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none',
          'active:scale-[0.98]',
          // Variant styles
          variantStyles[variant],
          // Size styles
          sizeStyles[size],
          // Full width
          fullWidth && 'w-full',
          className
        )}
        disabled={disabled || loading}
        aria-busy={loading}
        {...props}
      >
        {loading ? (
          <>
            <Spinner />
            <span className="sr-only">Loading...</span>
          </>
        ) : (
          <>
            {iconLeft && <span className="flex-shrink-0">{iconLeft}</span>}
            {children}
            {iconRight && <span className="flex-shrink-0">{iconRight}</span>}
          </>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';
