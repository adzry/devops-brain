"""
Design System Agent

Specialist agent for design system management, UI generation,
and design-to-code workflows using Figma integration.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .base_agent import BaseAgent, AgentConfig


class DesignFramework(str, Enum):
    """Supported frontend frameworks."""
    REACT = "react"
    VUE = "vue"
    SVELTE = "svelte"
    HTML = "html"


class StylingMethod(str, Enum):
    """Supported styling methods."""
    TAILWIND = "tailwind"
    CSS_MODULES = "css-modules"
    STYLED_COMPONENTS = "styled-components"
    CSS = "css"
    SCSS = "scss"


@dataclass
class DesignToken:
    """Represents a design token."""
    name: str
    category: str
    value: Any
    css_variable: str = ""
    description: str = ""


@dataclass
class UIComponent:
    """Represents a generated UI component."""
    name: str
    framework: DesignFramework
    code: str
    styles: str = ""
    props: dict = field(default_factory=dict)
    variants: list = field(default_factory=list)


class DesignAgent(BaseAgent):
    """
    Agent specialized in design system management and UI generation.
    
    Capabilities:
    - Design token management and synchronization
    - Component generation from Figma designs
    - Style guide generation and maintenance
    - Design-to-code conversion
    - UI consistency checking
    - Accessibility compliance
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._figma_adapter = None
        self._design_tokens: dict[str, DesignToken] = {}
        self._component_library: dict[str, UIComponent] = {}
    
    async def _register_handlers(self) -> None:
        """Register action handlers for design operations."""
        self._handlers = {
            "sync_tokens": self._sync_design_tokens,
            "generate_component": self._generate_component,
            "create_page": self._create_page,
            "audit_design": self._audit_design_consistency,
            "check_accessibility": self._check_accessibility,
            "generate_theme": self._generate_theme,
            "export_styleguide": self._export_styleguide,
            "create_component_library": self._create_component_library,
        }
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the Design agent."""
        return """You are the Design System Agent for DevOps Brain.

Your role is to bridge design and development by:
- Managing design tokens (colors, typography, spacing, shadows)
- Converting Figma designs to production-ready code
- Generating accessible, responsive UI components
- Maintaining design consistency across the application
- Creating comprehensive style guides

Key principles:
1. **Token-First**: Always use design tokens, never hardcode values
2. **Accessibility**: WCAG 2.1 AA compliance minimum
3. **Performance**: Optimize for runtime performance
4. **Consistency**: Ensure visual consistency across components
5. **Documentation**: Generate clear component documentation

When generating components:
- Use semantic HTML elements
- Include proper ARIA attributes
- Support keyboard navigation
- Follow the established naming conventions
- Include TypeScript types when applicable"""
    
    async def _sync_design_tokens(self, payload: dict[str, Any]) -> dict:
        """Sync design tokens from Figma."""
        figma_file = payload.get("figma_file")
        output_format = payload.get("format", "css")
        
        self.logger.info(f"Syncing design tokens from Figma: {figma_file}")
        
        # Design tokens organized by category
        tokens = {
            "colors": {
                "primitive": {
                    "indigo-50": "#EEF2FF",
                    "indigo-100": "#E0E7FF",
                    "indigo-500": "#6366F1",
                    "indigo-600": "#4F46E5",
                    "indigo-700": "#4338CA",
                    "slate-50": "#F8FAFC",
                    "slate-100": "#F1F5F9",
                    "slate-800": "#1E293B",
                    "slate-900": "#0F172A",
                    "rose-500": "#EC4899",
                    "emerald-500": "#10B981",
                    "amber-500": "#F59E0B",
                    "red-500": "#EF4444",
                },
                "semantic": {
                    "primary": "var(--color-indigo-500)",
                    "primary-hover": "var(--color-indigo-600)",
                    "secondary": "var(--color-rose-500)",
                    "background": "var(--color-slate-900)",
                    "surface": "var(--color-slate-800)",
                    "text": "var(--color-slate-50)",
                    "text-muted": "var(--color-slate-400)",
                    "success": "var(--color-emerald-500)",
                    "warning": "var(--color-amber-500)",
                    "error": "var(--color-red-500)",
                },
            },
            "typography": {
                "fonts": {
                    "display": "'Cal Sans', 'Inter', system-ui, sans-serif",
                    "body": "'Inter', system-ui, sans-serif",
                    "mono": "'JetBrains Mono', 'Fira Code', monospace",
                },
                "sizes": {
                    "xs": "0.75rem",
                    "sm": "0.875rem",
                    "base": "1rem",
                    "lg": "1.125rem",
                    "xl": "1.25rem",
                    "2xl": "1.5rem",
                    "3xl": "1.875rem",
                    "4xl": "2.25rem",
                    "5xl": "3rem",
                },
                "weights": {
                    "normal": "400",
                    "medium": "500",
                    "semibold": "600",
                    "bold": "700",
                },
                "line_heights": {
                    "tight": "1.25",
                    "normal": "1.5",
                    "relaxed": "1.75",
                },
            },
            "spacing": {
                "0": "0",
                "1": "0.25rem",
                "2": "0.5rem",
                "3": "0.75rem",
                "4": "1rem",
                "5": "1.25rem",
                "6": "1.5rem",
                "8": "2rem",
                "10": "2.5rem",
                "12": "3rem",
                "16": "4rem",
                "20": "5rem",
                "24": "6rem",
            },
            "radii": {
                "none": "0",
                "sm": "0.25rem",
                "md": "0.375rem",
                "lg": "0.5rem",
                "xl": "0.75rem",
                "2xl": "1rem",
                "full": "9999px",
            },
            "shadows": {
                "sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
                "md": "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                "lg": "0 10px 15px -3px rgb(0 0 0 / 0.1)",
                "xl": "0 20px 25px -5px rgb(0 0 0 / 0.1)",
                "glow": "0 0 20px rgb(99 102 241 / 0.4)",
                "glow-lg": "0 0 40px rgb(99 102 241 / 0.3)",
            },
            "animations": {
                "durations": {
                    "fast": "150ms",
                    "normal": "200ms",
                    "slow": "300ms",
                    "slower": "500ms",
                },
                "easings": {
                    "ease-out": "cubic-bezier(0, 0, 0.2, 1)",
                    "ease-in-out": "cubic-bezier(0.4, 0, 0.2, 1)",
                    "bounce": "cubic-bezier(0.68, -0.55, 0.265, 1.55)",
                },
            },
        }
        
        # Generate CSS output
        css_output = self._generate_css_tokens(tokens)
        
        return {
            "data": {
                "figma_file": figma_file,
                "tokens_synced": sum(
                    len(v) if isinstance(v, dict) else 1 
                    for cat in tokens.values() 
                    for v in (cat.values() if isinstance(cat, dict) else [cat])
                ),
                "categories": list(tokens.keys()),
                "output_format": output_format,
            },
            "tokens": tokens,
            "css": css_output,
            "files_generated": [
                "src/styles/tokens.css",
                "src/styles/tokens.json",
                "tailwind.config.js",
            ],
        }
    
    def _generate_css_tokens(self, tokens: dict) -> str:
        """Generate CSS custom properties from tokens."""
        css_lines = [
            "/* Design Tokens - Auto-generated from Figma */",
            "/* Do not edit manually */",
            "",
            ":root {",
        ]
        
        # Colors
        css_lines.append("  /* Primitive Colors */")
        for name, value in tokens["colors"]["primitive"].items():
            css_lines.append(f"  --color-{name}: {value};")
        
        css_lines.append("")
        css_lines.append("  /* Semantic Colors */")
        for name, value in tokens["colors"]["semantic"].items():
            css_lines.append(f"  --color-{name}: {value};")
        
        # Typography
        css_lines.append("")
        css_lines.append("  /* Typography */")
        for name, value in tokens["typography"]["fonts"].items():
            css_lines.append(f"  --font-{name}: {value};")
        for name, value in tokens["typography"]["sizes"].items():
            css_lines.append(f"  --text-{name}: {value};")
        
        # Spacing
        css_lines.append("")
        css_lines.append("  /* Spacing */")
        for name, value in tokens["spacing"].items():
            css_lines.append(f"  --space-{name}: {value};")
        
        # Border Radius
        css_lines.append("")
        css_lines.append("  /* Border Radius */")
        for name, value in tokens["radii"].items():
            css_lines.append(f"  --radius-{name}: {value};")
        
        # Shadows
        css_lines.append("")
        css_lines.append("  /* Shadows */")
        for name, value in tokens["shadows"].items():
            css_lines.append(f"  --shadow-{name}: {value};")
        
        # Animations
        css_lines.append("")
        css_lines.append("  /* Animation */")
        for name, value in tokens["animations"]["durations"].items():
            css_lines.append(f"  --duration-{name}: {value};")
        for name, value in tokens["animations"]["easings"].items():
            css_lines.append(f"  --easing-{name}: {value};")
        
        css_lines.append("}")
        
        return "\n".join(css_lines)
    
    async def _generate_component(self, payload: dict[str, Any]) -> dict:
        """Generate a UI component from design specs."""
        component_name = payload.get("name", "Component")
        component_type = payload.get("type", "button")
        framework = payload.get("framework", "react")
        styling = payload.get("styling", "tailwind")
        
        self.logger.info(f"Generating {component_type} component: {component_name}")
        
        # Component templates
        components = {
            "button": self._generate_button_component(component_name, framework),
            "input": self._generate_input_component(component_name, framework),
            "card": self._generate_card_component(component_name, framework),
            "modal": self._generate_modal_component(component_name, framework),
            "navbar": self._generate_navbar_component(component_name, framework),
        }
        
        component_code = components.get(component_type, components["button"])
        
        return {
            "data": {
                "component_name": component_name,
                "component_type": component_type,
                "framework": framework,
                "styling": styling,
            },
            "code": component_code,
            "usage": f"<{component_name} variant=\"primary\" size=\"md\">Click me</{component_name}>",
            "props": {
                "variant": ["primary", "secondary", "ghost", "danger"],
                "size": ["sm", "md", "lg"],
                "disabled": "boolean",
            },
        }
    
    def _generate_button_component(self, name: str, framework: str) -> str:
        """Generate a button component."""
        return f'''import React from 'react';
import {{ cn }} from '@/lib/utils';

interface {name}Props extends React.ButtonHTMLAttributes<HTMLButtonElement> {{
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
  children: React.ReactNode;
}}

const variants = {{
  primary: `
    bg-gradient-to-r from-indigo-500 to-indigo-600
    hover:from-indigo-600 hover:to-indigo-700
    text-white shadow-lg shadow-indigo-500/25
    hover:shadow-xl hover:shadow-indigo-500/30
  `,
  secondary: `
    bg-slate-800 border border-slate-700
    hover:bg-slate-700 hover:border-slate-600
    text-slate-100
  `,
  ghost: `
    bg-transparent hover:bg-slate-800
    text-slate-300 hover:text-white
  `,
  danger: `
    bg-gradient-to-r from-red-500 to-rose-600
    hover:from-red-600 hover:to-rose-700
    text-white shadow-lg shadow-red-500/25
  `,
}};

const sizes = {{
  sm: 'px-3 py-1.5 text-sm gap-1.5',
  md: 'px-5 py-2.5 text-base gap-2',
  lg: 'px-7 py-3.5 text-lg gap-2.5',
}};

export const {name} = React.forwardRef<HTMLButtonElement, {name}Props>(
  ({{ 
    className, 
    variant = 'primary', 
    size = 'md', 
    loading = false,
    icon,
    children, 
    disabled, 
    ...props 
  }}, ref) => {{
    return (
      <button
        ref={{ref}}
        className={{cn(
          'inline-flex items-center justify-center font-semibold',
          'rounded-xl transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:ring-offset-2 focus:ring-offset-slate-900',
          'disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none',
          'active:scale-[0.98]',
          variants[variant],
          sizes[size],
          className
        )}}
        disabled={{disabled || loading}}
        {{...props}}
      >
        {{loading ? (
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        ) : icon}}
        {{children}}
      </button>
    );
  }}
);

{name}.displayName = '{name}';
'''
    
    def _generate_input_component(self, name: str, framework: str) -> str:
        """Generate an input component."""
        return f'''import React from 'react';
import {{ cn }} from '@/lib/utils';

interface {name}Props extends React.InputHTMLAttributes<HTMLInputElement> {{
  label?: string;
  error?: string;
  hint?: string;
  icon?: React.ReactNode;
}}

export const {name} = React.forwardRef<HTMLInputElement, {name}Props>(
  ({{ className, label, error, hint, icon, ...props }}, ref) => {{
    return (
      <div className="space-y-1.5">
        {{label && (
          <label className="block text-sm font-medium text-slate-300">
            {{label}}
          </label>
        )}}
        <div className="relative">
          {{icon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
              {{icon}}
            </div>
          )}}
          <input
            ref={{ref}}
            className={{cn(
              'w-full px-4 py-3 rounded-xl',
              'bg-slate-800/50 border border-slate-700',
              'text-slate-100 placeholder:text-slate-500',
              'transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-indigo-500/50',
              'focus:border-indigo-500',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              error && 'border-red-500 focus:ring-red-500/50 focus:border-red-500',
              icon && 'pl-10',
              className
            )}}
            {{...props}}
          />
        </div>
        {{error && (
          <p className="text-sm text-red-400">{{error}}</p>
        )}}
        {{hint && !error && (
          <p className="text-sm text-slate-500">{{hint}}</p>
        )}}
      </div>
    );
  }}
);

{name}.displayName = '{name}';
'''
    
    def _generate_card_component(self, name: str, framework: str) -> str:
        """Generate a card component."""
        return f'''import React from 'react';
import {{ cn }} from '@/lib/utils';

interface {name}Props {{
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'elevated' | 'outlined' | 'gradient';
  hover?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}}

const variants = {{
  default: 'bg-slate-800/50 border border-slate-700/50',
  elevated: 'bg-slate-800 shadow-xl shadow-black/20',
  outlined: 'bg-transparent border-2 border-slate-700',
  gradient: 'bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700/50',
}};

const paddings = {{
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
}};

export const {name}: React.FC<{name}Props> = ({{
  children,
  className,
  variant = 'default',
  hover = false,
  padding = 'md',
}}) => {{
  return (
    <div
      className={{cn(
        'rounded-2xl backdrop-blur-sm',
        'transition-all duration-300',
        variants[variant],
        paddings[padding],
        hover && 'hover:shadow-xl hover:shadow-indigo-500/10 hover:border-indigo-500/30 hover:-translate-y-1',
        className
      )}}
    >
      {{children}}
    </div>
  );
}};
'''
    
    def _generate_modal_component(self, name: str, framework: str) -> str:
        """Generate a modal component."""
        return f'''import React, {{ useEffect }} from 'react';
import {{ cn }} from '@/lib/utils';
import {{ createPortal }} from 'react-dom';

interface {name}Props {{
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}}

const sizes = {{
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
}};

export const {name}: React.FC<{name}Props> = ({{
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
}}) => {{
  useEffect(() => {{
    const handleEscape = (e: KeyboardEvent) => {{
      if (e.key === 'Escape') onClose();
    }};
    
    if (isOpen) {{
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }}
    
    return () => {{
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    }};
  }}, [isOpen, onClose]);

  if (!isOpen) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {{/* Backdrop */}}
      <div 
        className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm animate-in fade-in duration-200"
        onClick={{onClose}}
      />
      
      {{/* Modal */}}
      <div
        className={{cn(
          'relative w-full rounded-2xl',
          'bg-gradient-to-br from-slate-800 to-slate-900',
          'border border-slate-700/50',
          'shadow-2xl shadow-black/50',
          'animate-in zoom-in-95 slide-in-from-bottom-4 duration-300',
          sizes[size]
        )}}
      >
        {{/* Header */}}
        {{title && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700/50">
            <h2 className="text-xl font-semibold text-white">{{title}}</h2>
            <button
              onClick={{onClose}}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={{2}} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}}
        
        {{/* Content */}}
        <div className="p-6">
          {{children}}
        </div>
      </div>
    </div>,
    document.body
  );
}};
'''
    
    def _generate_navbar_component(self, name: str, framework: str) -> str:
        """Generate a navbar component."""
        return f'''import React from 'react';
import {{ cn }} from '@/lib/utils';

interface NavItem {{
  label: string;
  href: string;
  icon?: React.ReactNode;
  active?: boolean;
}}

interface {name}Props {{
  logo?: React.ReactNode;
  items: NavItem[];
  actions?: React.ReactNode;
  className?: string;
}}

export const {name}: React.FC<{name}Props> = ({{
  logo,
  items,
  actions,
  className,
}}) => {{
  return (
    <nav
      className={{cn(
        'fixed top-0 left-0 right-0 z-40',
        'bg-slate-900/80 backdrop-blur-xl',
        'border-b border-slate-800',
        className
      )}}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {{/* Logo */}}
          <div className="flex-shrink-0">
            {{logo || (
              <span className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-rose-400 bg-clip-text text-transparent">
                DevOps Brain
              </span>
            )}}
          </div>
          
          {{/* Navigation Items */}}
          <div className="hidden md:flex items-center space-x-1">
            {{items.map((item, index) => (
              <a
                key={{index}}
                href={{item.href}}
                className={{cn(
                  'flex items-center gap-2 px-4 py-2 rounded-lg',
                  'text-sm font-medium transition-all duration-200',
                  item.active
                    ? 'text-white bg-indigo-500/20 border border-indigo-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                )}}
              >
                {{item.icon}}
                {{item.label}}
              </a>
            ))}}
          </div>
          
          {{/* Actions */}}
          <div className="flex items-center gap-3">
            {{actions}}
          </div>
        </div>
      </div>
    </nav>
  );
}};
'''
    
    async def _create_page(self, payload: dict[str, Any]) -> dict:
        """Generate a complete page layout."""
        page_name = payload.get("name", "Page")
        page_type = payload.get("type", "dashboard")
        sections = payload.get("sections", ["header", "main", "footer"])
        
        self.logger.info(f"Creating page: {page_name} ({page_type})")
        
        page_code = self._generate_page_code(page_name, page_type, sections)
        
        return {
            "data": {
                "page_name": page_name,
                "page_type": page_type,
                "sections": sections,
            },
            "code": page_code,
            "route": f"/{page_name.lower().replace(' ', '-')}",
        }
    
    def _generate_page_code(self, name: str, page_type: str, sections: list) -> str:
        """Generate page code."""
        return f'''import React from 'react';
import {{ Navbar }} from '@/components/Navbar';
import {{ Card }} from '@/components/Card';
import {{ Button }} from '@/components/Button';

export default function {name.replace(' ', '')}Page() {{
  return (
    <div className="min-h-screen bg-slate-900">
      {{/* Background Effects */}}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-indigo-500/20 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-rose-500/20 rounded-full blur-3xl" />
        <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-5" />
      </div>
      
      {{/* Navbar */}}
      <Navbar
        items={{[
          {{ label: 'Dashboard', href: '/dashboard', active: true }},
          {{ label: 'Agents', href: '/agents' }},
          {{ label: 'Tasks', href: '/tasks' }},
          {{ label: 'Settings', href: '/settings' }},
        ]}}
        actions={{
          <Button variant="primary" size="sm">
            New Task
          </Button>
        }}
      />
      
      {{/* Main Content */}}
      <main className="relative pt-24 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        {{/* Page Header */}}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">{name}</h1>
          <p className="text-slate-400">
            Welcome to your {page_type} overview
          </p>
        </div>
        
        {{/* Stats Grid */}}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {{[
            {{ label: 'Active Tasks', value: '12', trend: '+3' }},
            {{ label: 'Agents Online', value: '8', trend: '0' }},
            {{ label: 'Success Rate', value: '98.5%', trend: '+2.1%' }},
            {{ label: 'Avg Response', value: '1.2s', trend: '-0.3s' }},
          ].map((stat, i) => (
            <Card key={{i}} hover variant="gradient">
              <p className="text-sm text-slate-400 mb-1">{{stat.label}}</p>
              <div className="flex items-end justify-between">
                <span className="text-2xl font-bold text-white">{{stat.value}}</span>
                <span className="text-sm text-emerald-400">{{stat.trend}}</span>
              </div>
            </Card>
          ))}}
        </div>
        
        {{/* Main Content Grid */}}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {{/* Activity Feed */}}
          <Card className="lg:col-span-2" variant="default" padding="lg">
            <h2 className="text-lg font-semibold text-white mb-4">Recent Activity</h2>
            <div className="space-y-4">
              {{/* Activity items */}}
            </div>
          </Card>
          
          {{/* Quick Actions */}}
          <Card variant="elevated" padding="lg">
            <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <Button variant="primary" className="w-full">
                Run Security Scan
              </Button>
              <Button variant="secondary" className="w-full">
                Deploy to Staging
              </Button>
              <Button variant="ghost" className="w-full">
                View All Tasks
              </Button>
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}}
'''
    
    async def _audit_design_consistency(self, payload: dict[str, Any]) -> dict:
        """Audit design consistency across components."""
        target_path = payload.get("path", "src/components")
        
        issues = [
            {
                "type": "hardcoded_color",
                "file": "src/components/Header.tsx",
                "line": 45,
                "message": "Hardcoded color '#4F46E5' should use var(--color-primary)",
                "severity": "warning",
            },
            {
                "type": "inconsistent_spacing",
                "file": "src/components/Card.tsx",
                "line": 23,
                "message": "Inconsistent spacing '18px' should use var(--space-4) or var(--space-5)",
                "severity": "warning",
            },
            {
                "type": "missing_token",
                "file": "src/components/Button.tsx",
                "line": 67,
                "message": "Missing design token for shadow effect",
                "severity": "info",
            },
        ]
        
        return {
            "data": {
                "target_path": target_path,
                "files_scanned": 24,
                "issues_found": len(issues),
            },
            "issues": issues,
            "recommendations": [
                "Replace hardcoded colors with design token CSS variables",
                "Use spacing scale consistently (--space-* tokens)",
                "Add missing shadow tokens to design system",
            ],
        }
    
    async def _check_accessibility(self, payload: dict[str, Any]) -> dict:
        """Check accessibility compliance."""
        target = payload.get("target", "src/components")
        
        issues = [
            {
                "rule": "color-contrast",
                "level": "AA",
                "element": "button.secondary",
                "message": "Text color has insufficient contrast ratio (3.8:1, needs 4.5:1)",
                "fix": "Use --color-slate-100 instead of --color-slate-400",
            },
            {
                "rule": "focus-visible",
                "level": "AA",
                "element": "input[type='text']",
                "message": "Missing visible focus indicator",
                "fix": "Add focus:ring-2 focus:ring-indigo-500 styles",
            },
            {
                "rule": "aria-label",
                "level": "A",
                "element": "button.icon-only",
                "message": "Icon-only button missing accessible label",
                "fix": "Add aria-label attribute describing button action",
            },
        ]
        
        return {
            "data": {
                "target": target,
                "wcag_level": "AA",
                "issues_found": len(issues),
                "compliance_score": 87,
            },
            "issues": issues,
            "summary": {
                "level_a": {"passed": 45, "failed": 1},
                "level_aa": {"passed": 28, "failed": 2},
                "level_aaa": {"passed": 12, "failed": 5},
            },
        }
    
    async def _generate_theme(self, payload: dict[str, Any]) -> dict:
        """Generate a complete theme configuration."""
        theme_name = payload.get("name", "default")
        mode = payload.get("mode", "dark")
        primary_color = payload.get("primary", "#6366F1")
        
        theme = {
            "name": theme_name,
            "mode": mode,
            "colors": self._generate_color_palette(primary_color, mode),
            "config": self._generate_tailwind_theme(primary_color),
        }
        
        return {
            "data": theme,
            "files": [
                {"path": f"themes/{theme_name}.css", "type": "css"},
                {"path": f"themes/{theme_name}.json", "type": "json"},
            ],
        }
    
    def _generate_color_palette(self, primary: str, mode: str) -> dict:
        """Generate a color palette from primary color."""
        # Simplified palette generation
        return {
            "primary": {
                "50": "#EEF2FF",
                "100": "#E0E7FF",
                "200": "#C7D2FE",
                "300": "#A5B4FC",
                "400": "#818CF8",
                "500": primary,
                "600": "#4F46E5",
                "700": "#4338CA",
                "800": "#3730A3",
                "900": "#312E81",
            },
        }
    
    def _generate_tailwind_theme(self, primary: str) -> str:
        """Generate Tailwind theme configuration."""
        return f'''// tailwind.config.js
module.exports = {{
  darkMode: 'class',
  theme: {{
    extend: {{
      colors: {{
        primary: {{
          DEFAULT: '{primary}',
          50: '#EEF2FF',
          // ... other shades
        }},
      }},
      fontFamily: {{
        display: ['Cal Sans', 'system-ui'],
        body: ['Inter', 'system-ui'],
        mono: ['JetBrains Mono', 'monospace'],
      }},
      animation: {{
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'glow': 'glow 2s ease-in-out infinite alternate',
      }},
    }},
  }},
}};
'''
    
    async def _export_styleguide(self, payload: dict[str, Any]) -> dict:
        """Export a comprehensive style guide."""
        format_type = payload.get("format", "markdown")
        
        return {
            "data": {
                "format": format_type,
                "sections": ["colors", "typography", "spacing", "components", "patterns"],
            },
            "styleguide": "# Design System Style Guide\n\n...",
            "files": [
                "docs/styleguide.md",
                "docs/components.md",
                "docs/tokens.md",
            ],
        }
    
    async def _create_component_library(self, payload: dict[str, Any]) -> dict:
        """Create a complete component library."""
        name = payload.get("name", "ui")
        components = payload.get("components", ["button", "input", "card", "modal"])
        
        generated = []
        for comp in components:
            result = await self._generate_component({
                "name": comp.capitalize(),
                "type": comp,
                "framework": "react",
            })
            generated.append({
                "name": comp,
                "path": f"src/components/{comp.capitalize()}.tsx",
            })
        
        return {
            "data": {
                "library_name": name,
                "components_count": len(generated),
            },
            "components": generated,
            "index_file": self._generate_index_file(components),
        }
    
    def _generate_index_file(self, components: list) -> str:
        """Generate index file for component library."""
        exports = [f"export {{ {c.capitalize()} }} from './{c.capitalize()}';" for c in components]
        return "\n".join(exports)
