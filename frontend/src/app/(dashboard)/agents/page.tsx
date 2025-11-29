'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import useSWR from 'swr';
import {
  Bot,
  Shield,
  TestTube,
  FileText,
  Gauge,
  AlertTriangle,
  Database,
  Cloud,
  Palette,
  GitBranch,
  Play,
  Settings,
  MoreVertical,
} from 'lucide-react';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import api from '@/lib/api';
import { useStore } from '@/store';

// Icon mapping for agents
const agentIcons: Record<string, any> = {
  'root': Bot,
  'security': Shield,
  'testing': TestTube,
  'documentation': FileText,
  'performance': Gauge,
  'incident': AlertTriangle,
  'database': Database,
  'infrastructure': Cloud,
  'design': Palette,
  'deployment': GitBranch,
};

// Color mapping for agents
const agentColors: Record<string, string> = {
  'root': 'primary',
  'security': 'red',
  'testing': 'emerald',
  'documentation': 'blue',
  'performance': 'amber',
  'incident': 'orange',
  'database': 'violet',
  'infrastructure': 'cyan',
  'design': 'pink',
  'deployment': 'teal',
};

// Fallback agents data
const fallbackAgents = [
  {
    id: 'root',
    name: 'Root Agent',
    type: 'orchestrator',
    description: 'Primary orchestration agent for coordinating all DevOps tasks',
    icon: Bot,
    status: 'online',
    tasks_completed: 1247,
    success_rate: 99.2,
    capabilities: ['Task Routing', 'Agent Coordination', 'Workflow Orchestration'],
    color: 'primary',
  },
  {
    id: 'security',
    name: 'Security Agent',
    type: 'specialist',
    description: 'Vulnerability detection, compliance checking, and security advisory',
    icon: Shield,
    status: 'busy',
    tasks_completed: 892,
    success_rate: 98.7,
    capabilities: ['Vulnerability Scan', 'Secrets Detection', 'Compliance Check'],
    color: 'red',
  },
  {
    id: 'testing',
    name: 'Testing Agent',
    type: 'specialist',
    description: 'Test generation, execution, and coverage analysis',
    icon: TestTube,
    status: 'online',
    tasks_completed: 2341,
    success_rate: 97.8,
    capabilities: ['Test Generation', 'Coverage Analysis', 'Mutation Testing'],
    color: 'emerald',
  },
  {
    id: 'documentation',
    name: 'Documentation Agent',
    type: 'specialist',
    description: 'Automated documentation generation and maintenance',
    icon: FileText,
    status: 'online',
    tasks_completed: 567,
    success_rate: 99.5,
    capabilities: ['API Docs', 'README Generation', 'Changelog'],
    color: 'blue',
  },
  {
    id: 'performance',
    name: 'Performance Agent',
    type: 'specialist',
    description: 'Performance profiling, optimization, and load testing',
    icon: Gauge,
    status: 'online',
    tasks_completed: 423,
    success_rate: 96.4,
    capabilities: ['Profiling', 'Bottleneck Detection', 'Load Testing'],
    color: 'amber',
  },
  {
    id: 'incident',
    name: 'Incident Response Agent',
    type: 'specialist',
    description: 'Production incident handling and troubleshooting',
    icon: AlertTriangle,
    status: 'offline',
    tasks_completed: 189,
    success_rate: 94.2,
    capabilities: ['Incident Triage', 'Root Cause Analysis', 'Runbook Execution'],
    color: 'orange',
  },
  {
    id: 'database',
    name: 'Database Agent',
    type: 'specialist',
    description: 'Database optimization, migrations, and management',
    icon: Database,
    status: 'online',
    tasks_completed: 756,
    success_rate: 99.1,
    capabilities: ['Schema Design', 'Query Optimization', 'Migrations'],
    color: 'violet',
  },
  {
    id: 'infrastructure',
    name: 'Infrastructure Agent',
    type: 'specialist',
    description: 'Infrastructure as Code and cloud resource management',
    icon: Cloud,
    status: 'online',
    tasks_completed: 634,
    success_rate: 98.3,
    capabilities: ['Terraform', 'Kubernetes', 'Cost Optimization'],
    color: 'cyan',
  },
  {
    id: 'design',
    name: 'Design Agent',
    type: 'specialist',
    description: 'Design system management and UI component generation',
    icon: Palette,
    status: 'online',
    tasks_completed: 312,
    success_rate: 99.7,
    capabilities: ['Figma Sync', 'Component Generation', 'Accessibility'],
    color: 'pink',
  },
  {
    id: 'deployment',
    name: 'Deployment Agent',
    type: 'specialist',
    description: 'CI/CD pipeline management and deployment orchestration',
    icon: GitBranch,
    status: 'busy',
    tasks_completed: 1089,
    success_rate: 97.9,
    capabilities: ['Deployments', 'Rollbacks', 'Blue-Green Deploy'],
    color: 'teal',
  },
];

const colorClasses: Record<string, { bg: string; text: string; border: string }> = {
  primary: { bg: 'bg-primary-500/20', text: 'text-primary-400', border: 'border-primary-500/30' },
  red: { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30' },
  emerald: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500/30' },
  blue: { bg: 'bg-blue-500/20', text: 'text-blue-400', border: 'border-blue-500/30' },
  amber: { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/30' },
  orange: { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500/30' },
  violet: { bg: 'bg-violet-500/20', text: 'text-violet-400', border: 'border-violet-500/30' },
  cyan: { bg: 'bg-cyan-500/20', text: 'text-cyan-400', border: 'border-cyan-500/30' },
  pink: { bg: 'bg-pink-500/20', text: 'text-pink-400', border: 'border-pink-500/30' },
  teal: { bg: 'bg-teal-500/20', text: 'text-teal-400', border: 'border-teal-500/30' },
};

export default function AgentsPage() {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const { agents: storeAgents, setAgents } = useStore();

  // Fetch agents from API
  const { data: agentsData, error } = useSWR('/api/v1/agents', async () => {
    const response = await api.getAgents();
    if (response.error) {
      console.error('Failed to fetch agents:', response.error);
      return fallbackAgents;
    }
    const apiAgents = response.data || [];
    // Map API agents to display format
    const mappedAgents = apiAgents.map((agent: any) => {
      const nameLower = agent.name.toLowerCase();
      const iconKey = Object.keys(agentIcons).find(key => nameLower.includes(key)) || 'root';
      const colorKey = Object.keys(agentColors).find(key => nameLower.includes(key)) || 'primary';
      
      return {
        id: agent.name.toLowerCase().replace(/\s+/g, '_'),
        name: agent.name,
        type: agent.type || 'specialist',
        description: agent.description || `AI agent for ${agent.name}`,
        icon: agentIcons[iconKey] || Bot,
        status: agent.status || 'online',
        tasks_completed: 0, // Not available in API
        success_rate: 98.5, // Not available in API
        capabilities: agent.capabilities || [],
        color: agentColors[colorKey] || 'primary',
      };
    });
    
    if (mappedAgents.length > 0) {
      setAgents(response.data);
    }
    
    return mappedAgents.length > 0 ? mappedAgents : fallbackAgents;
  }, { refreshInterval: 10000 });

  const agents = agentsData || storeAgents.map((agent: any) => {
    const nameLower = agent.name?.toLowerCase() || '';
    const iconKey = Object.keys(agentIcons).find(key => nameLower.includes(key)) || 'root';
    const colorKey = Object.keys(agentColors).find(key => nameLower.includes(key)) || 'primary';
    
    return {
      id: agent.name?.toLowerCase().replace(/\s+/g, '_') || 'unknown',
      name: agent.name || 'Unknown Agent',
      type: agent.type || 'specialist',
      description: agent.description || `AI agent for ${agent.name}`,
      icon: agentIcons[iconKey] || Bot,
      status: agent.status || 'online',
      tasks_completed: agent.tasks_completed || 0,
      success_rate: agent.success_rate || 98.5,
      capabilities: agent.capabilities || [],
      color: agentColors[colorKey] || 'primary',
    };
  }) || fallbackAgents;

  return (
    <>
      <Header
        title="Agents"
        description="Manage and monitor your AI agents"
      />

      <div className="p-8">
        {/* Stats Summary */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <Card variant="glass" padding="md">
            <p className="text-sm text-slate-400">Total Agents</p>
            <p className="text-2xl font-bold text-white">{agents.length}</p>
          </Card>
          <Card variant="glass" padding="md">
            <p className="text-sm text-slate-400">Online</p>
            <p className="text-2xl font-bold text-emerald-400">
              {agents.filter(a => a.status === 'online').length}
            </p>
          </Card>
          <Card variant="glass" padding="md">
            <p className="text-sm text-slate-400">Busy</p>
            <p className="text-2xl font-bold text-amber-400">
              {agents.filter(a => a.status === 'busy').length}
            </p>
          </Card>
          <Card variant="glass" padding="md">
            <p className="text-sm text-slate-400">Offline</p>
            <p className="text-2xl font-bold text-slate-400">
              {agents.filter(a => a.status === 'offline').length}
            </p>
          </Card>
        </div>

        {/* Agents Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {agents.map((agent, i) => {
            const colors = colorClasses[agent.color];
            return (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <Card
                  variant="gradient"
                  hover
                  className={cn(
                    'relative overflow-hidden',
                    selectedAgent === agent.id && 'ring-2 ring-primary-500'
                  )}
                  onClick={() => setSelectedAgent(agent.id)}
                >
                  {/* Status Indicator */}
                  <div className="absolute top-4 right-4">
                    <Badge
                      variant={
                        agent.status === 'online' ? 'success' :
                        agent.status === 'busy' ? 'warning' : 'default'
                      }
                      dot
                    >
                      {agent.status}
                    </Badge>
                  </div>

                  {/* Agent Icon & Name */}
                  <div className="flex items-start gap-4 mb-4">
                    <div className={cn(
                      'p-3 rounded-xl',
                      colors.bg,
                      colors.text
                    )}>
                      <agent.icon className="w-6 h-6" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-semibold text-white truncate">{agent.name}</h3>
                      <p className="text-xs text-slate-500 uppercase tracking-wider">{agent.type}</p>
                    </div>
                  </div>

                  {/* Description */}
                  <p className="text-sm text-slate-400 mb-4 line-clamp-2">{agent.description}</p>

                  {/* Capabilities */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    {agent.capabilities.slice(0, 3).map((cap) => (
                      <span
                        key={cap}
                        className={cn(
                          'px-2 py-1 text-xs rounded-lg border',
                          colors.bg,
                          colors.text,
                          colors.border
                        )}
                      >
                        {cap}
                      </span>
                    ))}
                  </div>

                  {/* Stats */}
                  <div className="flex items-center justify-between pt-4 border-t border-slate-700/50">
                    <div>
                      <p className="text-xs text-slate-500">Tasks Completed</p>
                      <p className="text-lg font-semibold text-white">{agent.tasks_completed.toLocaleString()}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-slate-500">Success Rate</p>
                      <p className="text-lg font-semibold text-emerald-400">{agent.success_rate}%</p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 mt-4 pt-4 border-t border-slate-700/50">
                    <Button size="sm" variant="secondary" className="flex-1" icon={<Play className="w-4 h-4" />}>
                      Execute
                    </Button>
                    <Button size="sm" variant="ghost" icon={<Settings className="w-4 h-4" />} />
                    <Button size="sm" variant="ghost" icon={<MoreVertical className="w-4 h-4" />} />
                  </div>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </div>
    </>
  );
}
