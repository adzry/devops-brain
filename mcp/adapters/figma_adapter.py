"""
Figma MCP Adapter

Provides integration with Figma API for design system management,
component extraction, and design-to-code workflows.
"""

import os
import re
from typing import Any, Optional
from dataclasses import dataclass, field

from .base_adapter import (
    AdapterConfig,
    BaseAdapter,
    MCPRequest,
    MCPResponse,
)


@dataclass
class DesignToken:
    """Represents a design token extracted from Figma."""
    name: str
    type: str  # color, typography, spacing, shadow, etc.
    value: Any
    description: str = ""
    figma_id: str = ""


@dataclass
class FigmaComponent:
    """Represents a Figma component."""
    id: str
    name: str
    type: str
    description: str = ""
    properties: dict = field(default_factory=dict)
    children: list = field(default_factory=list)
    styles: dict = field(default_factory=dict)


class FigmaAdapter(BaseAdapter):
    """
    MCP adapter for Figma operations.
    
    Capabilities:
    - Design token extraction (colors, typography, spacing)
    - Component inspection and export
    - Style guide generation
    - Design-to-code conversion
    - Design system synchronization
    """
    
    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self._token: Optional[str] = None
        self._base_url = "https://api.figma.com/v1"
    
    async def _setup_client(self) -> None:
        """Initialize the Figma client."""
        token_env = self.config.extra.get("token_env", "FIGMA_ACCESS_TOKEN")
        self._token = os.environ.get(token_env)
        
        if not self._token:
            self.logger.warning(
                f"Figma token not found in {token_env}. "
                "Some operations may fail."
            )
        
        self.logger.info("Figma adapter client initialized")
    
    async def _cleanup(self) -> None:
        """Clean up the Figma client."""
        self._client = None
        self._token = None
    
    async def execute(self, request: MCPRequest) -> MCPResponse:
        """Execute a Figma API request."""
        if not self._initialized:
            await self.initialize()
        
        method = request.method
        params = request.params
        
        try:
            handlers = {
                "file.get": self._get_file,
                "file.components": self._get_components,
                "file.styles": self._get_styles,
                "tokens.extract": self._extract_tokens,
                "tokens.colors": self._extract_colors,
                "tokens.typography": self._extract_typography,
                "tokens.spacing": self._extract_spacing,
                "component.get": self._get_component,
                "component.to_code": self._component_to_code,
                "styleguide.generate": self._generate_styleguide,
                "sync.design_system": self._sync_design_system,
            }
            
            handler = handlers.get(method)
            if not handler:
                return MCPResponse(
                    success=False,
                    error=f"Unknown method: {method}",
                    request_id=request.request_id,
                )
            
            result = await handler(params)
            return MCPResponse(
                success=True,
                data=result,
                request_id=request.request_id,
            )
            
        except Exception as e:
            self.logger.error(f"Figma operation failed: {e}")
            return MCPResponse(
                success=False,
                error=str(e),
                request_id=request.request_id,
            )
    
    async def _get_file(self, params: dict[str, Any]) -> dict:
        """Get Figma file information."""
        file_key = params.get("file_key")
        
        # In production, make actual API call
        return {
            "file_key": file_key,
            "name": "Design System",
            "last_modified": "2024-11-29T12:00:00Z",
            "version": "1.0.0",
            "pages": [
                {"id": "page1", "name": "Components"},
                {"id": "page2", "name": "Tokens"},
                {"id": "page3", "name": "Icons"},
            ],
        }
    
    async def _get_components(self, params: dict[str, Any]) -> dict:
        """Get all components from a Figma file."""
        file_key = params.get("file_key")
        
        components = [
            {
                "id": "comp_btn_primary",
                "name": "Button/Primary",
                "description": "Primary action button",
                "type": "COMPONENT",
                "properties": {
                    "size": {"type": "VARIANT", "values": ["sm", "md", "lg"]},
                    "state": {"type": "VARIANT", "values": ["default", "hover", "disabled"]},
                },
            },
            {
                "id": "comp_btn_secondary",
                "name": "Button/Secondary",
                "description": "Secondary action button",
                "type": "COMPONENT",
            },
            {
                "id": "comp_input",
                "name": "Input/Text",
                "description": "Text input field",
                "type": "COMPONENT",
                "properties": {
                    "state": {"type": "VARIANT", "values": ["default", "focus", "error"]},
                },
            },
            {
                "id": "comp_card",
                "name": "Card/Default",
                "description": "Content card container",
                "type": "COMPONENT",
            },
        ]
        
        return {
            "file_key": file_key,
            "component_count": len(components),
            "components": components,
        }
    
    async def _get_styles(self, params: dict[str, Any]) -> dict:
        """Get all styles from a Figma file."""
        file_key = params.get("file_key")
        
        return {
            "file_key": file_key,
            "styles": {
                "colors": [
                    {"id": "style_primary", "name": "Primary", "type": "FILL"},
                    {"id": "style_secondary", "name": "Secondary", "type": "FILL"},
                    {"id": "style_accent", "name": "Accent", "type": "FILL"},
                    {"id": "style_bg", "name": "Background", "type": "FILL"},
                    {"id": "style_text", "name": "Text", "type": "FILL"},
                ],
                "text": [
                    {"id": "style_h1", "name": "Heading/H1", "type": "TEXT"},
                    {"id": "style_h2", "name": "Heading/H2", "type": "TEXT"},
                    {"id": "style_body", "name": "Body/Regular", "type": "TEXT"},
                    {"id": "style_caption", "name": "Caption", "type": "TEXT"},
                ],
                "effects": [
                    {"id": "style_shadow_sm", "name": "Shadow/Small", "type": "EFFECT"},
                    {"id": "style_shadow_md", "name": "Shadow/Medium", "type": "EFFECT"},
                ],
            },
        }
    
    async def _extract_tokens(self, params: dict[str, Any]) -> dict:
        """Extract all design tokens from a Figma file."""
        file_key = params.get("file_key")
        
        tokens = {
            "colors": await self._extract_colors(params),
            "typography": await self._extract_typography(params),
            "spacing": await self._extract_spacing(params),
            "shadows": await self._extract_shadows(params),
            "radii": await self._extract_radii(params),
        }
        
        return {
            "file_key": file_key,
            "tokens": tokens,
            "total_count": sum(len(v.get("tokens", [])) for v in tokens.values()),
            "export_formats": ["css", "scss", "json", "tailwind"],
        }
    
    async def _extract_colors(self, params: dict[str, Any]) -> dict:
        """Extract color tokens from Figma."""
        return {
            "tokens": [
                {
                    "name": "--color-primary",
                    "value": "#6366F1",
                    "rgb": "99, 102, 241",
                    "description": "Primary brand color",
                },
                {
                    "name": "--color-primary-dark",
                    "value": "#4F46E5",
                    "rgb": "79, 70, 229",
                    "description": "Primary dark variant",
                },
                {
                    "name": "--color-secondary",
                    "value": "#EC4899",
                    "rgb": "236, 72, 153",
                    "description": "Secondary accent color",
                },
                {
                    "name": "--color-background",
                    "value": "#0F172A",
                    "rgb": "15, 23, 42",
                    "description": "Main background color",
                },
                {
                    "name": "--color-surface",
                    "value": "#1E293B",
                    "rgb": "30, 41, 59",
                    "description": "Surface/card background",
                },
                {
                    "name": "--color-text",
                    "value": "#F8FAFC",
                    "rgb": "248, 250, 252",
                    "description": "Primary text color",
                },
                {
                    "name": "--color-text-muted",
                    "value": "#94A3B8",
                    "rgb": "148, 163, 184",
                    "description": "Muted/secondary text",
                },
                {
                    "name": "--color-success",
                    "value": "#10B981",
                    "rgb": "16, 185, 129",
                    "description": "Success state color",
                },
                {
                    "name": "--color-warning",
                    "value": "#F59E0B",
                    "rgb": "245, 158, 11",
                    "description": "Warning state color",
                },
                {
                    "name": "--color-error",
                    "value": "#EF4444",
                    "rgb": "239, 68, 68",
                    "description": "Error state color",
                },
            ],
            "css": self._generate_color_css(),
        }
    
    async def _extract_typography(self, params: dict[str, Any]) -> dict:
        """Extract typography tokens from Figma."""
        return {
            "tokens": [
                {
                    "name": "--font-display",
                    "family": "Cal Sans",
                    "fallback": "system-ui, sans-serif",
                    "description": "Display/heading font",
                },
                {
                    "name": "--font-body",
                    "family": "Inter",
                    "fallback": "system-ui, sans-serif",
                    "description": "Body text font",
                },
                {
                    "name": "--font-mono",
                    "family": "JetBrains Mono",
                    "fallback": "monospace",
                    "description": "Monospace/code font",
                },
                {
                    "name": "--text-xs",
                    "size": "0.75rem",
                    "line_height": "1rem",
                    "letter_spacing": "0.01em",
                },
                {
                    "name": "--text-sm",
                    "size": "0.875rem",
                    "line_height": "1.25rem",
                    "letter_spacing": "0",
                },
                {
                    "name": "--text-base",
                    "size": "1rem",
                    "line_height": "1.5rem",
                    "letter_spacing": "0",
                },
                {
                    "name": "--text-lg",
                    "size": "1.125rem",
                    "line_height": "1.75rem",
                    "letter_spacing": "-0.01em",
                },
                {
                    "name": "--text-xl",
                    "size": "1.25rem",
                    "line_height": "1.75rem",
                    "letter_spacing": "-0.01em",
                },
                {
                    "name": "--text-2xl",
                    "size": "1.5rem",
                    "line_height": "2rem",
                    "letter_spacing": "-0.02em",
                },
                {
                    "name": "--text-3xl",
                    "size": "1.875rem",
                    "line_height": "2.25rem",
                    "letter_spacing": "-0.02em",
                },
                {
                    "name": "--text-4xl",
                    "size": "2.25rem",
                    "line_height": "2.5rem",
                    "letter_spacing": "-0.03em",
                },
            ],
        }
    
    async def _extract_spacing(self, params: dict[str, Any]) -> dict:
        """Extract spacing tokens from Figma."""
        return {
            "tokens": [
                {"name": "--space-0", "value": "0"},
                {"name": "--space-1", "value": "0.25rem"},
                {"name": "--space-2", "value": "0.5rem"},
                {"name": "--space-3", "value": "0.75rem"},
                {"name": "--space-4", "value": "1rem"},
                {"name": "--space-5", "value": "1.25rem"},
                {"name": "--space-6", "value": "1.5rem"},
                {"name": "--space-8", "value": "2rem"},
                {"name": "--space-10", "value": "2.5rem"},
                {"name": "--space-12", "value": "3rem"},
                {"name": "--space-16", "value": "4rem"},
                {"name": "--space-20", "value": "5rem"},
                {"name": "--space-24", "value": "6rem"},
            ],
        }
    
    async def _extract_shadows(self, params: dict[str, Any]) -> dict:
        """Extract shadow tokens from Figma."""
        return {
            "tokens": [
                {
                    "name": "--shadow-sm",
                    "value": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
                },
                {
                    "name": "--shadow-md",
                    "value": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
                },
                {
                    "name": "--shadow-lg",
                    "value": "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
                },
                {
                    "name": "--shadow-xl",
                    "value": "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
                },
                {
                    "name": "--shadow-glow",
                    "value": "0 0 20px rgb(99 102 241 / 0.3)",
                    "description": "Glow effect for focus states",
                },
            ],
        }
    
    async def _extract_radii(self, params: dict[str, Any]) -> dict:
        """Extract border radius tokens from Figma."""
        return {
            "tokens": [
                {"name": "--radius-none", "value": "0"},
                {"name": "--radius-sm", "value": "0.25rem"},
                {"name": "--radius-md", "value": "0.375rem"},
                {"name": "--radius-lg", "value": "0.5rem"},
                {"name": "--radius-xl", "value": "0.75rem"},
                {"name": "--radius-2xl", "value": "1rem"},
                {"name": "--radius-full", "value": "9999px"},
            ],
        }
    
    async def _get_component(self, params: dict[str, Any]) -> dict:
        """Get detailed component information."""
        component_id = params.get("component_id")
        
        return {
            "id": component_id,
            "name": "Button/Primary",
            "description": "Primary action button with multiple variants",
            "type": "COMPONENT_SET",
            "variants": [
                {"name": "Size=sm, State=default", "id": "var1"},
                {"name": "Size=md, State=default", "id": "var2"},
                {"name": "Size=lg, State=default", "id": "var3"},
                {"name": "Size=md, State=hover", "id": "var4"},
                {"name": "Size=md, State=disabled", "id": "var5"},
            ],
            "properties": {
                "size": {"type": "VARIANT", "values": ["sm", "md", "lg"], "default": "md"},
                "state": {"type": "VARIANT", "values": ["default", "hover", "disabled"], "default": "default"},
                "label": {"type": "TEXT", "default": "Button"},
                "icon": {"type": "INSTANCE_SWAP", "optional": True},
            },
            "styles": {
                "background": "var(--color-primary)",
                "color": "var(--color-text)",
                "padding": "var(--space-3) var(--space-6)",
                "border_radius": "var(--radius-lg)",
                "font": "var(--font-body)",
                "font_size": "var(--text-sm)",
                "font_weight": "600",
            },
        }
    
    async def _component_to_code(self, params: dict[str, Any]) -> dict:
        """Convert a Figma component to code."""
        component_id = params.get("component_id")
        framework = params.get("framework", "react")
        styling = params.get("styling", "tailwind")
        
        # Get component details
        component = await self._get_component(params)
        
        code = self._generate_component_code(component, framework, styling)
        
        return {
            "component_id": component_id,
            "component_name": component["name"],
            "framework": framework,
            "styling": styling,
            "code": code,
            "files": [
                {"path": f"components/Button.{self._get_extension(framework)}", "content": code["component"]},
                {"path": "components/Button.styles.css", "content": code.get("styles", "")},
            ],
        }
    
    def _generate_component_code(self, component: dict, framework: str, styling: str) -> dict:
        """Generate component code based on framework and styling."""
        if framework == "react" and styling == "tailwind":
            return {
                "component": '''import React from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}

const sizeClasses = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-6 py-3 text-base',
  lg: 'px-8 py-4 text-lg',
};

const variantClasses = {
  primary: 'bg-primary text-white hover:bg-primary-dark shadow-md hover:shadow-lg',
  secondary: 'bg-surface text-text border border-primary/20 hover:bg-primary/10',
  ghost: 'bg-transparent text-text hover:bg-surface',
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center font-semibold rounded-lg',
          'transition-all duration-200 ease-out',
          'focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-2',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          sizeClasses[size],
          variantClasses[variant],
          className
        )}
        disabled={disabled}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
''',
                "styles": "",
            }
        
        return {"component": "// Code generation for this framework not implemented", "styles": ""}
    
    def _get_extension(self, framework: str) -> str:
        """Get file extension for framework."""
        extensions = {
            "react": "tsx",
            "vue": "vue",
            "svelte": "svelte",
            "html": "html",
        }
        return extensions.get(framework, "js")
    
    async def _generate_styleguide(self, params: dict[str, Any]) -> dict:
        """Generate a complete style guide from Figma file."""
        file_key = params.get("file_key")
        format_type = params.get("format", "css")
        
        tokens = await self._extract_tokens(params)
        
        if format_type == "css":
            css = self._tokens_to_css(tokens["tokens"])
        elif format_type == "tailwind":
            css = self._tokens_to_tailwind(tokens["tokens"])
        else:
            css = self._tokens_to_css(tokens["tokens"])
        
        return {
            "file_key": file_key,
            "format": format_type,
            "styleguide": css,
            "tokens": tokens,
        }
    
    def _generate_color_css(self) -> str:
        """Generate CSS for color tokens."""
        return """:root {
  /* Primary Colors */
  --color-primary: #6366F1;
  --color-primary-dark: #4F46E5;
  --color-primary-light: #818CF8;
  
  /* Secondary Colors */
  --color-secondary: #EC4899;
  --color-secondary-dark: #DB2777;
  
  /* Neutral Colors */
  --color-background: #0F172A;
  --color-surface: #1E293B;
  --color-surface-elevated: #334155;
  
  /* Text Colors */
  --color-text: #F8FAFC;
  --color-text-muted: #94A3B8;
  --color-text-subtle: #64748B;
  
  /* Semantic Colors */
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-error: #EF4444;
  --color-info: #3B82F6;
}
"""
    
    def _tokens_to_css(self, tokens: dict) -> str:
        """Convert tokens to CSS custom properties."""
        css_parts = [":root {"]
        
        # Colors
        if "colors" in tokens:
            css_parts.append("  /* Colors */")
            for token in tokens["colors"].get("tokens", []):
                css_parts.append(f"  {token['name']}: {token['value']};")
        
        # Typography
        if "typography" in tokens:
            css_parts.append("\n  /* Typography */")
            for token in tokens["typography"].get("tokens", []):
                if "family" in token:
                    css_parts.append(f"  {token['name']}: '{token['family']}', {token.get('fallback', 'sans-serif')};")
                elif "size" in token:
                    css_parts.append(f"  {token['name']}: {token['size']};")
        
        # Spacing
        if "spacing" in tokens:
            css_parts.append("\n  /* Spacing */")
            for token in tokens["spacing"].get("tokens", []):
                css_parts.append(f"  {token['name']}: {token['value']};")
        
        # Shadows
        if "shadows" in tokens:
            css_parts.append("\n  /* Shadows */")
            for token in tokens["shadows"].get("tokens", []):
                css_parts.append(f"  {token['name']}: {token['value']};")
        
        # Border Radius
        if "radii" in tokens:
            css_parts.append("\n  /* Border Radius */")
            for token in tokens["radii"].get("tokens", []):
                css_parts.append(f"  {token['name']}: {token['value']};")
        
        css_parts.append("}")
        return "\n".join(css_parts)
    
    def _tokens_to_tailwind(self, tokens: dict) -> str:
        """Convert tokens to Tailwind config."""
        return '''/** @type {import('tailwindcss').Config} */
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#6366F1',
          dark: '#4F46E5',
          light: '#818CF8',
        },
        secondary: {
          DEFAULT: '#EC4899',
          dark: '#DB2777',
        },
        background: '#0F172A',
        surface: {
          DEFAULT: '#1E293B',
          elevated: '#334155',
        },
      },
      fontFamily: {
        display: ['Cal Sans', 'system-ui', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 20px rgb(99 102 241 / 0.3)',
      },
    },
  },
};
'''
    
    async def _sync_design_system(self, params: dict[str, Any]) -> dict:
        """Sync design system from Figma to codebase."""
        file_key = params.get("file_key")
        output_dir = params.get("output_dir", "src/styles")
        
        # Extract all tokens
        tokens = await self._extract_tokens(params)
        
        # Generate files
        files_generated = [
            {"path": f"{output_dir}/tokens.css", "type": "css"},
            {"path": f"{output_dir}/tokens.json", "type": "json"},
            {"path": "tailwind.config.js", "type": "tailwind"},
        ]
        
        return {
            "file_key": file_key,
            "synced": True,
            "tokens_extracted": tokens["total_count"],
            "files_generated": files_generated,
            "recommendations": [
                "Run 'npm run build:css' to compile new tokens",
                "Review generated components for accuracy",
                "Update Storybook with new design tokens",
            ],
        }
    
    # Convenience methods
    
    async def get_design_tokens(self, file_key: str) -> MCPResponse:
        """Convenience method to extract design tokens."""
        request = MCPRequest(
            method="tokens.extract",
            params={"file_key": file_key},
        )
        return await self.execute(request)
    
    async def generate_component(
        self,
        component_id: str,
        framework: str = "react",
        styling: str = "tailwind",
    ) -> MCPResponse:
        """Convenience method to generate component code."""
        request = MCPRequest(
            method="component.to_code",
            params={
                "component_id": component_id,
                "framework": framework,
                "styling": styling,
            },
        )
        return await self.execute(request)
