import React from 'react';
import { cn } from './utils/cn';

export interface NavItem {
  /** Display label */
  label: string;
  /** Link URL */
  href: string;
  /** Optional icon */
  icon?: React.ReactNode;
  /** Whether this item is active */
  active?: boolean;
  /** Click handler */
  onClick?: () => void;
}

export interface NavbarProps {
  /** Logo element */
  logo?: React.ReactNode;
  /** Navigation items */
  items: NavItem[];
  /** Right-side actions */
  actions?: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
  /** Navbar variant */
  variant?: 'default' | 'transparent' | 'solid';
}

const BrainIcon = () => (
  <svg
    className="w-8 h-8"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    aria-hidden="true"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 00.659 1.591L19 14.5M14.25 3.104c.251.023.501.05.75.082M19 14.5l-2.47 2.47a3.12 3.12 0 01-2.21.916H9.68a3.12 3.12 0 01-2.21-.916L5 14.5m14 0V9a2.25 2.25 0 00-2.25-2.25H7.25A2.25 2.25 0 005 9v5.5"
    />
  </svg>
);

const variantStyles = {
  default: 'bg-slate-900/80 backdrop-blur-xl border-b border-slate-800',
  transparent: 'bg-transparent',
  solid: 'bg-slate-900 border-b border-slate-800',
};

export const Navbar: React.FC<NavbarProps> = ({
  logo,
  items,
  actions,
  className,
  variant = 'default',
}) => {
  return (
    <nav
      className={cn(
        'fixed top-0 left-0 right-0 z-40',
        variantStyles[variant],
        className
      )}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex-shrink-0">
            {logo || (
              <a href="/" className="flex items-center gap-3 group">
                <div className="text-indigo-500 group-hover:text-indigo-400 transition-colors">
                  <BrainIcon />
                </div>
                <span
                  className={cn(
                    'text-xl font-bold',
                    'bg-gradient-to-r from-indigo-400 via-rose-400 to-indigo-400',
                    'bg-clip-text text-transparent',
                    'bg-[length:200%_auto]',
                    'group-hover:animate-gradient'
                  )}
                >
                  DevOps Brain
                </span>
              </a>
            )}
          </div>

          {/* Navigation Items - Desktop */}
          <div className="hidden md:flex items-center space-x-1">
            {items.map((item, index) => (
              <a
                key={index}
                href={item.href}
                onClick={item.onClick}
                className={cn(
                  'flex items-center gap-2 px-4 py-2 rounded-lg',
                  'text-sm font-medium transition-all duration-200',
                  item.active
                    ? [
                        'text-white',
                        'bg-indigo-500/20',
                        'border border-indigo-500/30',
                      ]
                    : [
                        'text-slate-400',
                        'hover:text-white',
                        'hover:bg-slate-800',
                      ]
                )}
                aria-current={item.active ? 'page' : undefined}
              >
                {item.icon && (
                  <span className="w-4 h-4" aria-hidden="true">
                    {item.icon}
                  </span>
                )}
                {item.label}
              </a>
            ))}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3">
            {actions}

            {/* Mobile menu button */}
            <button
              className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              aria-label="Toggle menu"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};
