'use client';

import React, { useState, useEffect } from 'react';
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
import api, { type Agent } from '@/lib/api';
import { useStore } from '@/store';

const agentIcons: Record<string, typeof Bot> = {
  'root_agent': Bot,
  'security_agent': Shield,
  'testing_agent': TestTube,
  'documentation_agent': FileText,
  'performance_agent': Gauge,
  'incident_response_agent': AlertTriangle,
  'database_agent': Database,
  'infrastructure_agent': Cloud,
  'design_agent': Palette,
  'deployment_agent': GitBranch,
};

const colorClasses: Record<string, { bg: string; text: string; border: string }> = {
  root: { bg: 'bg-primary-500/20', text: 'text-primary-400', border: 'border-primary-500/30' },
  security: { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30' },
  testing: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500/30' },
  documentation: { bg: 'bg-blue-500/20', text: 'text-blue-400', border: 'border-blue-500/30' },
  performance: { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/30' },
  incident: { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500/30' },
  database: { bg: 'bg-violet-500/20', text: 'text-violet-400', border: 'border-violet-500/30' },
  infrastructure: { bg: 'bg-cyan-500/20', text: 'text-cyan-400', border: 'border-cyan-500/30' },
  design: { bg: 'bg-pink-500/20', text: 'text-pink-400', border: 'border-pink-500/30' },
  deployment: { bg: 'bg-teal-500/20', text: 'text-teal-400', border: 'border-teal-500/30' },
  primary: { bg: 'bg-primary-500/20', text: 'text-primary-400', border: 'border-primary-500/30' },
};

export default function AgentsPage() {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const { agents, setAgents } = useStore();

  // Fetch agents
  const { data: agentsData, mutate: mutateAgents } = useSWR('/api/v1/agents', () => api.getAgents(), {
    refreshInterval: 5000,
  });

  useEffect(() => {
    if (agentsData?.data) {
      setAgents(agentsData.data);
    }
  }, [agentsData, setAgents]);

  const handleExecute = async (agentName: string, action: string) => {
    try {
      await api.executeAgentAction(agentName, action, {});
      mutateAgents();
    } catch (error) {
      console.error('Failed to execute action:', error);
    }
  };

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
          {agents.length > 0 ? (
            agents.map((agent, i) => {
              const Icon = agentIcons[agent.name] || Bot;
              const colorKey = agent.name.split('_')[0] || 'primary';
              const colors = colorClasses[colorKey] || colorClasses.primary;
              
              return (
                <motion.div
                  key={agent.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Card
                    variant="gradient"
                    hover
                    className={cn(
                      'relative overflow-hidden',
                      selectedAgent === agent.name && 'ring-2 ring-primary-500'
                    )}
                    onClick={() => setSelectedAgent(agent.name)}
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
                        <Icon className="w-6 h-6" />
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
                        <p className="text-xs text-slate-500">Active Tasks</p>
                        <p className="text-lg font-semibold text-white">{agent.active_tasks || 0}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-slate-500">Priority</p>
                        <p className="text-lg font-semibold text-emerald-400">{agent.priority || 0}</p>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 mt-4 pt-4 border-t border-slate-700/50">
                      <Button 
                        size="sm" 
                        variant="secondary" 
                        className="flex-1" 
                        icon={<Play className="w-4 h-4" />}
                        onClick={(e) => {
                          e.stopPropagation();
                          if (agent.capabilities.length > 0) {
                            handleExecute(agent.name, agent.capabilities[0]);
                          }
                        }}
                      >
                        Execute
                      </Button>
                      <Button size="sm" variant="ghost" icon={<Settings className="w-4 h-4" />} />
                      <Button size="sm" variant="ghost" icon={<MoreVertical className="w-4 h-4" />} />
                    </div>
                  </Card>
                </motion.div>
              );
            })
          ) : (
            <div className="col-span-full text-center py-12 text-slate-400">
              No agents available
            </div>
          )}
        </div>
      </div>
    </>
  );
}
