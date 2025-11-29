'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Palette,
  Type,
  Layers,
  Square,
  Sun,
  Moon,
  Copy,
  Check,
  RefreshCw,
  Download,
  Figma,
  Code,
  Eye,
} from 'lucide-react';
import { Header } from '@/components/layout/Header';
import { Card, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { cn } from '@/lib/utils';

// Color tokens
const colors = {
  primary: [
    { name: 'primary-50', value: '#EEF2FF' },
    { name: 'primary-100', value: '#E0E7FF' },
    { name: 'primary-200', value: '#C7D2FE' },
    { name: 'primary-300', value: '#A5B4FC' },
    { name: 'primary-400', value: '#818CF8' },
    { name: 'primary-500', value: '#6366F1' },
    { name: 'primary-600', value: '#4F46E5' },
    { name: 'primary-700', value: '#4338CA' },
    { name: 'primary-800', value: '#3730A3' },
    { name: 'primary-900', value: '#312E81' },
  ],
  secondary: [
    { name: 'secondary-400', value: '#FB7185' },
    { name: 'secondary-500', value: '#F43F5E' },
    { name: 'secondary-600', value: '#E11D48' },
  ],
  semantic: [
    { name: 'success', value: '#10B981' },
    { name: 'warning', value: '#F59E0B' },
    { name: 'error', value: '#EF4444' },
    { name: 'info', value: '#3B82F6' },
  ],
  neutral: [
    { name: 'background', value: '#0F172A' },
    { name: 'surface', value: '#1E293B' },
    { name: 'border', value: '#334155' },
    { name: 'text', value: '#F8FAFC' },
    { name: 'muted', value: '#94A3B8' },
  ],
};

// Typography tokens
const typography = {
  fonts: [
    { name: 'Display', value: 'Cal Sans', sample: 'The quick brown fox' },
    { name: 'Body', value: 'Inter', sample: 'The quick brown fox jumps over the lazy dog' },
    { name: 'Mono', value: 'JetBrains Mono', sample: 'const code = "clean";' },
  ],
  sizes: [
    { name: 'xs', value: '0.75rem', px: '12px' },
    { name: 'sm', value: '0.875rem', px: '14px' },
    { name: 'base', value: '1rem', px: '16px' },
    { name: 'lg', value: '1.125rem', px: '18px' },
    { name: 'xl', value: '1.25rem', px: '20px' },
    { name: '2xl', value: '1.5rem', px: '24px' },
    { name: '3xl', value: '1.875rem', px: '30px' },
    { name: '4xl', value: '2.25rem', px: '36px' },
  ],
};

// Spacing tokens
const spacing = [
  { name: '1', value: '0.25rem', px: '4px' },
  { name: '2', value: '0.5rem', px: '8px' },
  { name: '3', value: '0.75rem', px: '12px' },
  { name: '4', value: '1rem', px: '16px' },
  { name: '6', value: '1.5rem', px: '24px' },
  { name: '8', value: '2rem', px: '32px' },
  { name: '12', value: '3rem', px: '48px' },
  { name: '16', value: '4rem', px: '64px' },
];

// Radius tokens
const radii = [
  { name: 'sm', value: '0.25rem' },
  { name: 'md', value: '0.375rem' },
  { name: 'lg', value: '0.5rem' },
  { name: 'xl', value: '0.75rem' },
  { name: '2xl', value: '1rem' },
  { name: 'full', value: '9999px' },
];

// Component for copying values
const CopyButton: React.FC<{ value: string }> = ({ value }) => {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={copy}
      className="p-1 rounded text-slate-500 hover:text-white transition-colors"
    >
      {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
    </button>
  );
};

export default function DesignPage() {
  const [activeTab, setActiveTab] = useState<'colors' | 'typography' | 'spacing' | 'components'>('colors');
  const [figmaKey, setFigmaKey] = useState('');

  const tabs = [
    { id: 'colors', label: 'Colors', icon: Palette },
    { id: 'typography', label: 'Typography', icon: Type },
    { id: 'spacing', label: 'Spacing', icon: Layers },
    { id: 'components', label: 'Components', icon: Square },
  ];

  return (
    <>
      <Header title="Design System" description="Manage design tokens and UI components" />

      <div className="p-8">
        {/* Figma Sync Card */}
        <Card variant="gradient" className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-[#1E1E1E]">
                <Figma className="w-8 h-8 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">Figma Integration</h3>
                <p className="text-sm text-slate-400">Sync design tokens directly from your Figma file</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Input
                placeholder="Figma file key..."
                value={figmaKey}
                onChange={(e) => setFigmaKey(e.target.value)}
                className="w-64"
              />
              <Button icon={<RefreshCw className="w-4 h-4" />}>
                Sync Tokens
              </Button>
            </div>
          </div>
        </Card>

        {/* Tabs */}
        <div className="flex items-center gap-2 mb-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={cn(
                'flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all',
                activeTab === tab.id
                  ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              )}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}

          <div className="ml-auto flex items-center gap-2">
            <Button variant="secondary" size="sm" icon={<Code className="w-4 h-4" />}>
              Export CSS
            </Button>
            <Button variant="secondary" size="sm" icon={<Download className="w-4 h-4" />}>
              Download JSON
            </Button>
          </div>
        </div>

        {/* Colors Tab */}
        {activeTab === 'colors' && (
          <div className="space-y-8">
            {/* Primary Colors */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Primary</h3>
              <div className="grid grid-cols-10 gap-2">
                {colors.primary.map((color, i) => (
                  <motion.div
                    key={color.name}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.03 }}
                    className="group"
                  >
                    <div
                      className="aspect-square rounded-xl mb-2 ring-1 ring-white/10 group-hover:ring-white/30 transition-all"
                      style={{ backgroundColor: color.value }}
                    />
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-400">{color.name.split('-')[1]}</span>
                      <CopyButton value={color.value} />
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Secondary Colors */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Secondary</h3>
              <div className="grid grid-cols-10 gap-2">
                {colors.secondary.map((color, i) => (
                  <motion.div
                    key={color.name}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.03 }}
                    className="group"
                  >
                    <div
                      className="aspect-square rounded-xl mb-2 ring-1 ring-white/10"
                      style={{ backgroundColor: color.value }}
                    />
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-400">{color.name.split('-')[1]}</span>
                      <CopyButton value={color.value} />
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Semantic Colors */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Semantic</h3>
              <div className="grid grid-cols-4 gap-4">
                {colors.semantic.map((color, i) => (
                  <motion.div
                    key={color.name}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                  >
                    <Card variant="glass" padding="sm" className="flex items-center gap-3">
                      <div
                        className="w-10 h-10 rounded-lg"
                        style={{ backgroundColor: color.value }}
                      />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-white capitalize">{color.name}</p>
                        <p className="text-xs text-slate-500">{color.value}</p>
                      </div>
                      <CopyButton value={color.value} />
                    </Card>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Neutral Colors */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Neutrals</h3>
              <div className="grid grid-cols-5 gap-4">
                {colors.neutral.map((color, i) => (
                  <motion.div
                    key={color.name}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                  >
                    <Card variant="glass" padding="sm" className="flex items-center gap-3">
                      <div
                        className="w-10 h-10 rounded-lg ring-1 ring-white/10"
                        style={{ backgroundColor: color.value }}
                      />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-white capitalize">{color.name}</p>
                        <p className="text-xs text-slate-500">{color.value}</p>
                      </div>
                      <CopyButton value={color.value} />
                    </Card>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Typography Tab */}
        {activeTab === 'typography' && (
          <div className="space-y-8">
            {/* Font Families */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Font Families</h3>
              <div className="space-y-4">
                {typography.fonts.map((font, i) => (
                  <motion.div
                    key={font.name}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                  >
                    <Card variant="glass">
                      <div className="flex items-center justify-between mb-2">
                        <Badge variant="primary">{font.name}</Badge>
                        <span className="text-sm text-slate-500 font-mono">{font.value}</span>
                      </div>
                      <p
                        className="text-2xl text-white"
                        style={{ fontFamily: font.value }}
                      >
                        {font.sample}
                      </p>
                    </Card>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Font Sizes */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Font Sizes</h3>
              <Card variant="default" padding="none">
                <div className="divide-y divide-slate-700/50">
                  {typography.sizes.map((size, i) => (
                    <motion.div
                      key={size.name}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.03 }}
                      className="flex items-center justify-between px-6 py-4"
                    >
                      <div className="flex items-center gap-4">
                        <Badge variant="default">text-{size.name}</Badge>
                        <span className="text-slate-500 text-sm">{size.value} / {size.px}</span>
                      </div>
                      <span style={{ fontSize: size.value }} className="text-white">
                        The quick brown fox
                      </span>
                    </motion.div>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        )}

        {/* Spacing Tab */}
        {activeTab === 'spacing' && (
          <div className="space-y-8">
            {/* Spacing Scale */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Spacing Scale</h3>
              <Card variant="default" padding="none">
                <div className="divide-y divide-slate-700/50">
                  {spacing.map((space, i) => (
                    <motion.div
                      key={space.name}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.03 }}
                      className="flex items-center gap-6 px-6 py-4"
                    >
                      <Badge variant="default">space-{space.name}</Badge>
                      <span className="text-slate-500 text-sm w-24">{space.value}</span>
                      <span className="text-slate-500 text-sm w-16">{space.px}</span>
                      <div className="flex-1">
                        <div
                          className="h-4 bg-primary-500/50 rounded"
                          style={{ width: space.px }}
                        />
                      </div>
                    </motion.div>
                  ))}
                </div>
              </Card>
            </div>

            {/* Border Radius */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Border Radius</h3>
              <div className="grid grid-cols-6 gap-4">
                {radii.map((radius, i) => (
                  <motion.div
                    key={radius.name}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.05 }}
                  >
                    <Card variant="glass" padding="md" className="text-center">
                      <div
                        className="w-16 h-16 mx-auto mb-3 bg-primary-500/50 border-2 border-primary-500"
                        style={{ borderRadius: radius.value }}
                      />
                      <Badge variant="default">rounded-{radius.name}</Badge>
                      <p className="text-xs text-slate-500 mt-1">{radius.value}</p>
                    </Card>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Components Tab */}
        {activeTab === 'components' && (
          <div className="space-y-8">
            {/* Buttons */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Buttons</h3>
              <Card variant="glass">
                <div className="flex flex-wrap gap-4">
                  <Button variant="primary">Primary</Button>
                  <Button variant="secondary">Secondary</Button>
                  <Button variant="ghost">Ghost</Button>
                  <Button variant="danger">Danger</Button>
                  <Button variant="primary" loading>Loading</Button>
                  <Button variant="primary" disabled>Disabled</Button>
                </div>
                <div className="flex flex-wrap gap-4 mt-4 pt-4 border-t border-slate-700/50">
                  <Button size="sm">Small</Button>
                  <Button size="md">Medium</Button>
                  <Button size="lg">Large</Button>
                </div>
              </Card>
            </div>

            {/* Badges */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Badges</h3>
              <Card variant="glass">
                <div className="flex flex-wrap gap-3">
                  <Badge variant="default">Default</Badge>
                  <Badge variant="primary">Primary</Badge>
                  <Badge variant="success">Success</Badge>
                  <Badge variant="warning">Warning</Badge>
                  <Badge variant="error">Error</Badge>
                  <Badge variant="info">Info</Badge>
                </div>
                <div className="flex flex-wrap gap-3 mt-4 pt-4 border-t border-slate-700/50">
                  <Badge variant="success" dot>With Dot</Badge>
                  <Badge variant="warning" dot>Status</Badge>
                  <Badge variant="error" dot>Alert</Badge>
                </div>
              </Card>
            </div>

            {/* Inputs */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Inputs</h3>
              <Card variant="glass">
                <div className="grid grid-cols-2 gap-4">
                  <Input label="Default Input" placeholder="Enter text..." />
                  <Input label="With Error" placeholder="Enter text..." error="This field is required" />
                  <Input label="With Hint" placeholder="Enter email..." hint="We'll never share your email" />
                  <Input label="Disabled" placeholder="Can't edit this" disabled />
                </div>
              </Card>
            </div>

            {/* Cards */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Cards</h3>
              <div className="grid grid-cols-4 gap-4">
                <Card variant="default">
                  <CardTitle>Default</CardTitle>
                  <CardDescription>Basic card style</CardDescription>
                </Card>
                <Card variant="elevated">
                  <CardTitle>Elevated</CardTitle>
                  <CardDescription>With shadow</CardDescription>
                </Card>
                <Card variant="glass">
                  <CardTitle>Glass</CardTitle>
                  <CardDescription>Frosted effect</CardDescription>
                </Card>
                <Card variant="gradient">
                  <CardTitle>Gradient</CardTitle>
                  <CardDescription>Subtle gradient</CardDescription>
                </Card>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
