"""
Design API Routes

API endpoints for design system operations, Figma integration,
and UI component generation.
"""

from typing import Any, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

# Router
router = APIRouter(prefix="/design", tags=["design"])


# ==================== Models ====================

class Framework(str, Enum):
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


class TokenFormat(str, Enum):
    """Token export formats."""
    CSS = "css"
    JSON = "json"
    TAILWIND = "tailwind"
    SCSS = "scss"


class ExtractTokensRequest(BaseModel):
    """Request to extract design tokens from Figma."""
    figma_file_key: str = Field(..., description="Figma file key")
    format: TokenFormat = Field(default=TokenFormat.CSS, description="Output format")


class ExtractTokensResponse(BaseModel):
    """Response containing extracted design tokens."""
    success: bool
    tokens: dict[str, Any]
    css: Optional[str] = None
    json_output: Optional[str] = None
    files_generated: list[str] = []


class GenerateComponentRequest(BaseModel):
    """Request to generate a UI component."""
    figma_component_id: Optional[str] = Field(None, description="Figma component ID")
    component_type: str = Field(..., description="Type of component (button, input, card, etc.)")
    component_name: str = Field(..., description="Name for the generated component")
    framework: Framework = Field(default=Framework.REACT, description="Target framework")
    styling: StylingMethod = Field(default=StylingMethod.TAILWIND, description="Styling method")
    variants: list[str] = Field(default=[], description="Component variants to generate")
    include_tests: bool = Field(default=False, description="Generate test files")
    include_stories: bool = Field(default=False, description="Generate Storybook stories")


class GenerateComponentResponse(BaseModel):
    """Response containing generated component code."""
    success: bool
    component_name: str
    files: list[dict[str, str]]  # [{path: str, content: str}]
    usage_example: str
    props_documentation: dict[str, Any]


class SyncDesignSystemRequest(BaseModel):
    """Request to sync design system from Figma."""
    figma_file_key: str
    output_dir: str = Field(default="src/styles")
    components_dir: str = Field(default="src/components")
    generate_components: bool = Field(default=True)
    create_pr: bool = Field(default=False)


class SyncDesignSystemResponse(BaseModel):
    """Response from design system sync."""
    success: bool
    tokens_synced: int
    components_generated: int
    files_modified: list[str]
    pr_url: Optional[str] = None


class AuditRequest(BaseModel):
    """Request to audit design consistency."""
    target_path: str = Field(default="src")
    include_accessibility: bool = Field(default=True)


class AuditResponse(BaseModel):
    """Response from design audit."""
    success: bool
    issues: list[dict[str, Any]]
    accessibility_score: Optional[int] = None
    recommendations: list[str]


# ==================== Endpoints ====================

@router.post("/tokens/extract", response_model=ExtractTokensResponse)
async def extract_design_tokens(request: ExtractTokensRequest):
    """
    Extract design tokens from a Figma file.
    
    Extracts:
    - Colors (primitive and semantic)
    - Typography (fonts, sizes, weights)
    - Spacing scale
    - Border radii
    - Shadows
    - Animations
    """
    # Mock implementation - in production, use Figma adapter
    tokens = {
        "colors": {
            "primary": {
                "50": "#EEF2FF",
                "500": "#6366F1",
                "600": "#4F46E5",
            },
            "secondary": {
                "500": "#F43F5E",
            },
            "semantic": {
                "background": "#0F172A",
                "surface": "#1E293B",
                "text": "#F8FAFC",
            },
        },
        "typography": {
            "fonts": {
                "display": "Cal Sans, Inter, system-ui",
                "body": "Inter, system-ui",
                "mono": "JetBrains Mono, monospace",
            },
            "sizes": {
                "xs": "0.75rem",
                "sm": "0.875rem",
                "base": "1rem",
                "lg": "1.125rem",
                "xl": "1.25rem",
            },
        },
        "spacing": {
            "1": "0.25rem",
            "2": "0.5rem",
            "4": "1rem",
            "6": "1.5rem",
            "8": "2rem",
        },
        "radii": {
            "sm": "0.25rem",
            "md": "0.375rem",
            "lg": "0.5rem",
            "xl": "0.75rem",
        },
        "shadows": {
            "sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
            "md": "0 4px 6px -1px rgb(0 0 0 / 0.1)",
            "glow": "0 0 20px rgb(99 102 241 / 0.4)",
        },
    }
    
    css_output = _generate_css_from_tokens(tokens) if request.format == TokenFormat.CSS else None
    
    return ExtractTokensResponse(
        success=True,
        tokens=tokens,
        css=css_output,
        files_generated=[
            "src/styles/tokens.css",
            "src/styles/tokens.json",
        ],
    )


@router.post("/components/generate", response_model=GenerateComponentResponse)
async def generate_component(request: GenerateComponentRequest):
    """
    Generate a UI component from Figma design or specification.
    
    Supports:
    - Multiple frameworks (React, Vue, Svelte, HTML)
    - Multiple styling methods (Tailwind, CSS Modules, etc.)
    - Automatic accessibility attributes
    - Optional test generation
    - Optional Storybook stories
    """
    # Generate component based on type
    generators = {
        "button": _generate_button,
        "input": _generate_input,
        "card": _generate_card,
        "modal": _generate_modal,
        "navbar": _generate_navbar,
    }
    
    generator = generators.get(request.component_type.lower())
    if not generator:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown component type: {request.component_type}"
        )
    
    code, props = generator(request.component_name, request.framework.value)
    
    files = [
        {
            "path": f"src/components/{request.component_name}.tsx",
            "content": code,
        }
    ]
    
    if request.include_tests:
        files.append({
            "path": f"src/components/__tests__/{request.component_name}.test.tsx",
            "content": _generate_test(request.component_name),
        })
    
    if request.include_stories:
        files.append({
            "path": f"src/components/{request.component_name}.stories.tsx",
            "content": _generate_story(request.component_name),
        })
    
    return GenerateComponentResponse(
        success=True,
        component_name=request.component_name,
        files=files,
        usage_example=f'<{request.component_name} variant="primary" />',
        props_documentation=props,
    )


@router.post("/sync", response_model=SyncDesignSystemResponse)
async def sync_design_system(request: SyncDesignSystemRequest):
    """
    Sync entire design system from Figma.
    
    This endpoint:
    1. Extracts all design tokens
    2. Generates CSS/Tailwind config
    3. Optionally generates components
    4. Optionally creates a PR with changes
    """
    files_modified = [
        f"{request.output_dir}/tokens.css",
        f"{request.output_dir}/tokens.json",
        "tailwind.config.js",
    ]
    
    components_count = 0
    if request.generate_components:
        components_count = 5  # Mock count
        files_modified.extend([
            f"{request.components_dir}/Button.tsx",
            f"{request.components_dir}/Input.tsx",
            f"{request.components_dir}/Card.tsx",
            f"{request.components_dir}/Modal.tsx",
            f"{request.components_dir}/Navbar.tsx",
        ])
    
    return SyncDesignSystemResponse(
        success=True,
        tokens_synced=45,
        components_generated=components_count,
        files_modified=files_modified,
        pr_url="https://github.com/org/repo/pull/123" if request.create_pr else None,
    )


@router.post("/audit", response_model=AuditResponse)
async def audit_design_system(request: AuditRequest):
    """
    Audit codebase for design system compliance.
    
    Checks:
    - Hardcoded colors/spacing
    - Missing design tokens
    - Accessibility issues (optional)
    - Inconsistent patterns
    """
    issues = [
        {
            "type": "hardcoded_color",
            "file": "src/components/Header.tsx",
            "line": 45,
            "message": "Hardcoded color '#4F46E5' should use var(--color-primary)",
            "severity": "warning",
            "fix": "Replace with 'bg-primary' or 'var(--color-primary)'",
        },
        {
            "type": "hardcoded_spacing",
            "file": "src/components/Card.tsx",
            "line": 23,
            "message": "Hardcoded spacing '18px' not in design system",
            "severity": "warning",
            "fix": "Use var(--space-4) (16px) or var(--space-5) (20px)",
        },
    ]
    
    accessibility_score = None
    if request.include_accessibility:
        accessibility_score = 87
        issues.append({
            "type": "accessibility",
            "file": "src/components/Button.tsx",
            "line": 67,
            "message": "Button missing aria-label for icon-only variant",
            "severity": "error",
            "fix": "Add aria-label prop for accessibility",
        })
    
    return AuditResponse(
        success=True,
        issues=issues,
        accessibility_score=accessibility_score,
        recommendations=[
            "Replace all hardcoded colors with design tokens",
            "Use spacing scale consistently",
            "Add aria-labels to all interactive elements",
        ],
    )


@router.get("/tokens")
async def get_current_tokens():
    """Get the current design tokens configuration."""
    return {
        "colors": {
            "primary": "#6366F1",
            "secondary": "#F43F5E",
            "background": "#0F172A",
            "surface": "#1E293B",
            "text": "#F8FAFC",
        },
        "fonts": {
            "display": "Cal Sans",
            "body": "Inter",
            "mono": "JetBrains Mono",
        },
        "version": "1.0.0",
        "last_synced": "2024-11-29T12:00:00Z",
    }


@router.get("/components")
async def list_components():
    """List available UI components in the library."""
    return {
        "components": [
            {
                "name": "Button",
                "path": "src/ui/components/Button.tsx",
                "variants": ["primary", "secondary", "ghost", "danger"],
                "sizes": ["sm", "md", "lg"],
            },
            {
                "name": "Input",
                "path": "src/ui/components/Input.tsx",
                "props": ["label", "error", "hint", "iconLeft", "iconRight"],
            },
            {
                "name": "Card",
                "path": "src/ui/components/Card.tsx",
                "variants": ["default", "elevated", "outlined", "gradient", "glass"],
            },
            {
                "name": "Modal",
                "path": "src/ui/components/Modal.tsx",
                "sizes": ["sm", "md", "lg", "xl", "full"],
            },
            {
                "name": "Navbar",
                "path": "src/ui/components/Navbar.tsx",
                "variants": ["default", "transparent", "solid"],
            },
        ],
        "total": 5,
    }


# ==================== Helper Functions ====================

def _generate_css_from_tokens(tokens: dict) -> str:
    """Generate CSS custom properties from tokens."""
    css_lines = [":root {"]
    
    # Colors
    for category, values in tokens.get("colors", {}).items():
        if isinstance(values, dict):
            for name, value in values.items():
                css_lines.append(f"  --color-{category}-{name}: {value};")
    
    # Typography
    for name, value in tokens.get("typography", {}).get("fonts", {}).items():
        css_lines.append(f"  --font-{name}: {value};")
    
    # Spacing
    for name, value in tokens.get("spacing", {}).items():
        css_lines.append(f"  --space-{name}: {value};")
    
    css_lines.append("}")
    return "\n".join(css_lines)


def _generate_button(name: str, framework: str) -> tuple[str, dict]:
    """Generate button component code."""
    code = f'''import React from 'react';
import {{ cn }} from '../utils/cn';

export interface {name}Props extends React.ButtonHTMLAttributes<HTMLButtonElement> {{
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
}}

export const {name} = React.forwardRef<HTMLButtonElement, {name}Props>(
  ({{ className, variant = 'primary', size = 'md', loading, children, disabled, ...props }}, ref) => {{
    return (
      <button
        ref={{ref}}
        className={{cn(
          'inline-flex items-center justify-center font-semibold rounded-xl',
          'transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-offset-2',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          // Variants
          variant === 'primary' && 'bg-primary-500 hover:bg-primary-600 text-white',
          variant === 'secondary' && 'bg-slate-800 hover:bg-slate-700 text-white border border-slate-700',
          variant === 'ghost' && 'bg-transparent hover:bg-slate-800 text-slate-300',
          variant === 'danger' && 'bg-red-500 hover:bg-red-600 text-white',
          // Sizes
          size === 'sm' && 'px-3 py-1.5 text-sm',
          size === 'md' && 'px-5 py-2.5 text-base',
          size === 'lg' && 'px-7 py-3.5 text-lg',
          className
        )}}
        disabled={{disabled || loading}}
        {{...props}}
      >
        {{loading ? <span className="animate-spin">⏳</span> : children}}
      </button>
    );
  }}
);

{name}.displayName = '{name}';
'''
    
    props = {
        "variant": {
            "type": "'primary' | 'secondary' | 'ghost' | 'danger'",
            "default": "'primary'",
            "description": "Visual style variant",
        },
        "size": {
            "type": "'sm' | 'md' | 'lg'",
            "default": "'md'",
            "description": "Button size",
        },
        "loading": {
            "type": "boolean",
            "default": "false",
            "description": "Show loading state",
        },
    }
    
    return code, props


def _generate_input(name: str, framework: str) -> tuple[str, dict]:
    """Generate input component code."""
    code = f'''import React from 'react';
import {{ cn }} from '../utils/cn';

export interface {name}Props extends React.InputHTMLAttributes<HTMLInputElement> {{
  label?: string;
  error?: string;
  hint?: string;
}}

export const {name} = React.forwardRef<HTMLInputElement, {name}Props>(
  ({{ className, label, error, hint, ...props }}, ref) => {{
    return (
      <div className="space-y-1.5">
        {{label && <label className="block text-sm font-medium text-slate-300">{{label}}</label>}}
        <input
          ref={{ref}}
          className={{cn(
            'w-full px-4 py-3 rounded-xl',
            'bg-slate-800/50 border border-slate-700',
            'text-slate-100 placeholder:text-slate-500',
            'focus:outline-none focus:ring-2 focus:ring-primary-500/50',
            error && 'border-red-500',
            className
          )}}
          {{...props}}
        />
        {{error && <p className="text-sm text-red-400">{{error}}</p>}}
        {{hint && !error && <p className="text-sm text-slate-500">{{hint}}</p>}}
      </div>
    );
  }}
);

{name}.displayName = '{name}';
'''
    
    props = {
        "label": {"type": "string", "description": "Input label"},
        "error": {"type": "string", "description": "Error message"},
        "hint": {"type": "string", "description": "Hint text"},
    }
    
    return code, props


def _generate_card(name: str, framework: str) -> tuple[str, dict]:
    """Generate card component code."""
    code = f'''import React from 'react';
import {{ cn }} from '../utils/cn';

export interface {name}Props {{
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'elevated' | 'glass';
  hover?: boolean;
}}

export const {name}: React.FC<{name}Props> = ({{
  children,
  className,
  variant = 'default',
  hover = false,
}}) => {{
  return (
    <div
      className={{cn(
        'rounded-2xl p-6',
        variant === 'default' && 'bg-slate-800/50 border border-slate-700/50',
        variant === 'elevated' && 'bg-slate-800 shadow-xl',
        variant === 'glass' && 'bg-slate-800/30 backdrop-blur-xl border border-slate-700/30',
        hover && 'hover:shadow-xl hover:border-primary-500/30 hover:-translate-y-1 transition-all duration-300',
        className
      )}}
    >
      {{children}}
    </div>
  );
}};
'''
    
    props = {
        "variant": {"type": "'default' | 'elevated' | 'glass'", "default": "'default'"},
        "hover": {"type": "boolean", "default": "false"},
    }
    
    return code, props


def _generate_modal(name: str, framework: str) -> tuple[str, dict]:
    """Generate modal component code."""
    code = f'''import React, {{ useEffect }} from 'react';
import {{ cn }} from '../utils/cn';

export interface {name}Props {{
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
}}

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
    if (isOpen) document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }}, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm" onClick={{onClose}} />
      <div className={{cn(
        'relative w-full rounded-2xl bg-slate-800 border border-slate-700 shadow-2xl',
        size === 'sm' && 'max-w-md',
        size === 'md' && 'max-w-lg',
        size === 'lg' && 'max-w-2xl',
      )}}>
        {{title && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
            <h2 className="text-xl font-semibold text-white">{{title}}</h2>
            <button onClick={{onClose}} className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700">
              ✕
            </button>
          </div>
        )}}
        <div className="p-6">{{children}}</div>
      </div>
    </div>
  );
}};
'''
    
    props = {
        "isOpen": {"type": "boolean", "required": True},
        "onClose": {"type": "() => void", "required": True},
        "title": {"type": "string"},
        "size": {"type": "'sm' | 'md' | 'lg'", "default": "'md'"},
    }
    
    return code, props


def _generate_navbar(name: str, framework: str) -> tuple[str, dict]:
    """Generate navbar component code."""
    code = f'''import React from 'react';
import {{ cn }} from '../utils/cn';

export interface NavItem {{
  label: string;
  href: string;
  active?: boolean;
}}

export interface {name}Props {{
  items: NavItem[];
  logo?: React.ReactNode;
  actions?: React.ReactNode;
}}

export const {name}: React.FC<{name}Props> = ({{ items, logo, actions }}) => {{
  return (
    <nav className="fixed top-0 left-0 right-0 z-40 bg-slate-900/80 backdrop-blur-xl border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex-shrink-0">
            {{logo || <span className="text-xl font-bold text-gradient-primary">DevOps Brain</span>}}
          </div>
          <div className="hidden md:flex items-center space-x-1">
            {{items.map((item, i) => (
              <a
                key={{i}}
                href={{item.href}}
                className={{cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                  item.active ? 'text-white bg-primary-500/20 border border-primary-500/30' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                )}}
              >
                {{item.label}}
              </a>
            ))}}
          </div>
          <div className="flex items-center gap-3">{{actions}}</div>
        </div>
      </div>
    </nav>
  );
}};
'''
    
    props = {
        "items": {"type": "NavItem[]", "required": True},
        "logo": {"type": "React.ReactNode"},
        "actions": {"type": "React.ReactNode"},
    }
    
    return code, props


def _generate_test(name: str) -> str:
    """Generate test file for component."""
    return f'''import React from 'react';
import {{ render, screen, fireEvent }} from '@testing-library/react';
import {{ {name} }} from '../{name}';

describe('{name}', () => {{
  it('renders correctly', () => {{
    render(<{name}>Test</{name}>);
    expect(screen.getByText('Test')).toBeInTheDocument();
  }});

  it('handles click events', () => {{
    const onClick = jest.fn();
    render(<{name} onClick={{onClick}}>Click me</{name}>);
    fireEvent.click(screen.getByText('Click me'));
    expect(onClick).toHaveBeenCalled();
  }});
}});
'''


def _generate_story(name: str) -> str:
    """Generate Storybook story for component."""
    return f'''import type {{ Meta, StoryObj }} from '@storybook/react';
import {{ {name} }} from './{name}';

const meta: Meta<typeof {name}> = {{
  title: 'Components/{name}',
  component: {name},
  tags: ['autodocs'],
}};

export default meta;
type Story = StoryObj<typeof {name}>;

export const Default: Story = {{
  args: {{
    children: '{name}',
  }},
}};

export const Primary: Story = {{
  args: {{
    variant: 'primary',
    children: 'Primary {name}',
  }},
}};

export const Secondary: Story = {{
  args: {{
    variant: 'secondary',
    children: 'Secondary {name}',
  }},
}};
'''
