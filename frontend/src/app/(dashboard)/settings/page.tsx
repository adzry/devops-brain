'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Settings,
  User,
  Bell,
  Shield,
  Palette,
  Globe,
  Key,
  Database,
  Cloud,
  Save,
  RefreshCw,
} from 'lucide-react';
import { Header } from '@/components/layout/Header';
import { Card, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';

const settingsSections = [
  { id: 'general', label: 'General', icon: Settings },
  { id: 'api-keys', label: 'API Keys', icon: Key },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'integrations', label: 'Integrations', icon: Globe },
];

const integrations = [
  {
    name: 'GitHub',
    description: 'Repository and PR management',
    icon: '🐙',
    connected: true,
    account: 'org/devops-brain',
  },
  {
    name: 'Slack',
    description: 'Notifications and incidents',
    icon: '💬',
    connected: true,
    account: '#devops-alerts',
  },
  {
    name: 'Figma',
    description: 'Design token synchronization',
    icon: '🎨',
    connected: false,
    account: null,
  },
  {
    name: 'AWS',
    description: 'Cloud infrastructure',
    icon: '☁️',
    connected: true,
    account: 'prod-account',
  },
  {
    name: 'Datadog',
    description: 'Monitoring and metrics',
    icon: '📊',
    connected: false,
    account: null,
  },
];

export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState('general');
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsSaving(false);
  };

  return (
    <>
      <Header title="Settings" description="Configure your DevOps Brain instance" />

      <div className="p-8">
        <div className="flex gap-8">
          {/* Sidebar Navigation */}
          <div className="w-64 flex-shrink-0">
            <nav className="space-y-1">
              {settingsSections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={cn(
                    'w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all',
                    activeSection === section.id
                      ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  )}
                >
                  <section.icon className="w-5 h-5" />
                  {section.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1 max-w-3xl">
            {/* General Settings */}
            {activeSection === 'general' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                <Card variant="default">
                  <CardTitle>Instance Configuration</CardTitle>
                  <CardDescription>Basic settings for your DevOps Brain instance</CardDescription>

                  <div className="mt-6 space-y-4">
                    <Input label="Instance Name" defaultValue="DevOps Brain Production" />
                    <Input label="API Base URL" defaultValue="https://api.devops-brain.io" />
                    <Input
                      label="Default Timeout (seconds)"
                      type="number"
                      defaultValue="300"
                      hint="Maximum time for task execution"
                    />
                  </div>
                </Card>

                <Card variant="default">
                  <CardTitle>Agent Configuration</CardTitle>
                  <CardDescription>Default settings for AI agents</CardDescription>

                  <div className="mt-6 space-y-4">
                    <Input
                      label="Max Concurrent Agents"
                      type="number"
                      defaultValue="5"
                    />
                    <Input
                      label="Retry Attempts"
                      type="number"
                      defaultValue="3"
                    />
                    <div className="flex items-center justify-between py-3">
                      <div>
                        <p className="text-sm font-medium text-white">Auto-scaling</p>
                        <p className="text-xs text-slate-500">Automatically scale agents based on load</p>
                      </div>
                      <button className="relative w-12 h-6 bg-primary-500 rounded-full transition-colors">
                        <span className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full transition-transform" />
                      </button>
                    </div>
                  </div>
                </Card>
              </motion.div>
            )}

            {/* API Keys */}
            {activeSection === 'api-keys' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                <Card variant="default">
                  <CardTitle>API Keys</CardTitle>
                  <CardDescription>Manage your API keys for external services</CardDescription>

                  <div className="mt-6 space-y-4">
                    <Input
                      label="OpenAI API Key"
                      type="password"
                      defaultValue="sk-••••••••••••••••••••••••"
                      icon={<Key className="w-4 h-4" />}
                    />
                    <Input
                      label="Anthropic API Key"
                      type="password"
                      placeholder="Enter your Anthropic API key"
                      icon={<Key className="w-4 h-4" />}
                    />
                    <Input
                      label="GitHub Token"
                      type="password"
                      defaultValue="ghp_••••••••••••••••••••"
                      icon={<Key className="w-4 h-4" />}
                    />
                    <Input
                      label="Figma Access Token"
                      type="password"
                      placeholder="Enter your Figma access token"
                      icon={<Key className="w-4 h-4" />}
                    />
                  </div>
                </Card>

                <Card variant="glass" padding="md">
                  <div className="flex items-center gap-3">
                    <Shield className="w-5 h-5 text-emerald-400" />
                    <div>
                      <p className="text-sm font-medium text-white">Secure Storage</p>
                      <p className="text-xs text-slate-400">All API keys are encrypted at rest</p>
                    </div>
                  </div>
                </Card>
              </motion.div>
            )}

            {/* Notifications */}
            {activeSection === 'notifications' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                <Card variant="default">
                  <CardTitle>Notification Preferences</CardTitle>
                  <CardDescription>Configure how you receive updates</CardDescription>

                  <div className="mt-6 space-y-4">
                    {[
                      { label: 'Task Completed', desc: 'When a task finishes successfully' },
                      { label: 'Task Failed', desc: 'When a task encounters an error' },
                      { label: 'Security Alerts', desc: 'Critical security findings' },
                      { label: 'System Updates', desc: 'New features and updates' },
                    ].map((item) => (
                      <div key={item.label} className="flex items-center justify-between py-3 border-b border-slate-700/50 last:border-0">
                        <div>
                          <p className="text-sm font-medium text-white">{item.label}</p>
                          <p className="text-xs text-slate-500">{item.desc}</p>
                        </div>
                        <button className="relative w-12 h-6 bg-primary-500 rounded-full transition-colors">
                          <span className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full" />
                        </button>
                      </div>
                    ))}
                  </div>
                </Card>
              </motion.div>
            )}

            {/* Integrations */}
            {activeSection === 'integrations' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                <Card variant="default" padding="none">
                  <div className="p-6 border-b border-slate-700/50">
                    <CardTitle>Connected Services</CardTitle>
                    <CardDescription>Manage your external integrations</CardDescription>
                  </div>

                  <div className="divide-y divide-slate-700/50">
                    {integrations.map((integration) => (
                      <div key={integration.name} className="px-6 py-4 flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="text-3xl">{integration.icon}</div>
                          <div>
                            <p className="text-sm font-medium text-white">{integration.name}</p>
                            <p className="text-xs text-slate-500">{integration.description}</p>
                            {integration.account && (
                              <p className="text-xs text-slate-400 mt-1">Connected: {integration.account}</p>
                            )}
                          </div>
                        </div>
                        {integration.connected ? (
                          <Badge variant="success" dot>Connected</Badge>
                        ) : (
                          <Button size="sm" variant="secondary">Connect</Button>
                        )}
                      </div>
                    ))}
                  </div>
                </Card>
              </motion.div>
            )}

            {/* Save Button */}
            <div className="mt-8 flex justify-end gap-3">
              <Button variant="ghost" icon={<RefreshCw className="w-4 h-4" />}>
                Reset
              </Button>
              <Button
                onClick={handleSave}
                loading={isSaving}
                icon={<Save className="w-4 h-4" />}
              >
                Save Changes
              </Button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
