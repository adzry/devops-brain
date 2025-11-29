'use client';

import React, { useState } from 'react';
import { Play, Bot, Zap, Shield, TestTube, FileText, Palette, Database, Cloud } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';
import { useStore } from '@/store';
import api from '@/lib/api';

const taskTemplates = [
  {
    id: 'security-scan',
    name: 'Security Scan',
    description: 'Scan for vulnerabilities',
    icon: Shield,
    action: 'scan_vulnerabilities',
    agent: 'Security Agent',
    color: 'red',
  },
  {
    id: 'run-tests',
    name: 'Run Tests',
    description: 'Execute test suite',
    icon: TestTube,
    action: 'run_tests',
    agent: 'Testing Agent',
    color: 'emerald',
  },
  {
    id: 'generate-docs',
    name: 'Generate Docs',
    description: 'Update documentation',
    icon: FileText,
    action: 'generate_documentation',
    agent: 'Documentation Agent',
    color: 'blue',
  },
  {
    id: 'sync-design',
    name: 'Sync Design',
    description: 'Sync Figma tokens',
    icon: Palette,
    action: 'sync_tokens',
    agent: 'Design Agent',
    color: 'violet',
  },
  {
    id: 'db-migrate',
    name: 'DB Migration',
    description: 'Run migrations',
    icon: Database,
    action: 'run_migration',
    agent: 'Database Agent',
    color: 'amber',
  },
  {
    id: 'infra-plan',
    name: 'Infra Plan',
    description: 'Terraform plan',
    icon: Cloud,
    action: 'terraform_plan',
    agent: 'Infrastructure Agent',
    color: 'cyan',
  },
];

const colorClasses: Record<string, { bg: string; text: string }> = {
  red: { bg: 'bg-red-500/20', text: 'text-red-400' },
  emerald: { bg: 'bg-emerald-500/20', text: 'text-emerald-400' },
  blue: { bg: 'bg-blue-500/20', text: 'text-blue-400' },
  violet: { bg: 'bg-violet-500/20', text: 'text-violet-400' },
  amber: { bg: 'bg-amber-500/20', text: 'text-amber-400' },
  cyan: { bg: 'bg-cyan-500/20', text: 'text-cyan-400' },
};

export const NewTaskModal: React.FC = () => {
  const { modalOpen, closeModal, addTask } = useStore();
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [customAction, setCustomAction] = useState('');
  const [target, setTarget] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isOpen = modalOpen === 'new-task';

  const handleSubmit = async () => {
    const template = taskTemplates.find((t) => t.id === selectedTemplate);
    const action = template?.action || customAction;

    if (!action) return;

    setIsSubmitting(true);

    try {
      const response = await api.submitTask(action, {
        target: target || undefined,
      });

      if (response.data) {
        addTask({
          id: response.data.task_id,
          action,
          agent: template?.agent || 'Auto-assigned',
          status: 'pending',
          created_at: new Date().toISOString(),
        });
      }

      closeModal();
      setSelectedTemplate(null);
      setCustomAction('');
      setTarget('');
    } catch (error) {
      console.error('Failed to submit task:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={closeModal}
      title="Create New Task"
      description="Select a template or create a custom task"
      size="lg"
      footer={
        <>
          <Button variant="ghost" onClick={closeModal}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            loading={isSubmitting}
            disabled={!selectedTemplate && !customAction}
            icon={<Play className="w-4 h-4" />}
          >
            Execute Task
          </Button>
        </>
      }
    >
      <div className="space-y-6">
        {/* Task Templates */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-3">
            Quick Actions
          </label>
          <div className="grid grid-cols-3 gap-3">
            {taskTemplates.map((template) => {
              const colors = colorClasses[template.color];
              const isSelected = selectedTemplate === template.id;

              return (
                <button
                  key={template.id}
                  onClick={() => {
                    setSelectedTemplate(template.id);
                    setCustomAction('');
                  }}
                  className={cn(
                    'p-4 rounded-xl text-left transition-all',
                    'border-2',
                    isSelected
                      ? 'border-primary-500 bg-primary-500/10'
                      : 'border-slate-700 hover:border-slate-600 bg-slate-800/50'
                  )}
                >
                  <div className={cn('p-2 rounded-lg w-fit mb-2', colors.bg)}>
                    <template.icon className={cn('w-5 h-5', colors.text)} />
                  </div>
                  <p className="text-sm font-medium text-white">{template.name}</p>
                  <p className="text-xs text-slate-500">{template.description}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Divider */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-700" />
          </div>
          <div className="relative flex justify-center text-xs">
            <span className="px-2 bg-slate-800 text-slate-500">or create custom</span>
          </div>
        </div>

        {/* Custom Action */}
        <div className="space-y-4">
          <Input
            label="Custom Action"
            placeholder="e.g., analyze_performance, generate_report"
            value={customAction}
            onChange={(e) => {
              setCustomAction(e.target.value);
              setSelectedTemplate(null);
            }}
            hint="Enter a custom action name for the agent to execute"
          />

          <Input
            label="Target (Optional)"
            placeholder="e.g., src/, main branch, production"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            hint="Specify a target path, branch, or environment"
          />
        </div>

        {/* Selected Task Preview */}
        {(selectedTemplate || customAction) && (
          <Card variant="glass" padding="md">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-primary-500/20">
                  <Zap className="w-5 h-5 text-primary-400" />
                </div>
                <div>
                  <p className="text-sm font-medium text-white">
                    {taskTemplates.find((t) => t.id === selectedTemplate)?.action || customAction}
                  </p>
                  <p className="text-xs text-slate-500">
                    Agent: {taskTemplates.find((t) => t.id === selectedTemplate)?.agent || 'Auto-assigned'}
                  </p>
                </div>
              </div>
              <Badge variant="primary">Ready</Badge>
            </div>
          </Card>
        )}
      </div>
    </Modal>
  );
};
