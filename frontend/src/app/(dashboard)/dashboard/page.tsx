'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import useSWR from 'swr';
import {
  Activity,
  Bot,
  CheckCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Zap,
  Shield,
  Palette,
  Database,
  GitBranch,
} from 'lucide-react';
import { Header } from '@/components/layout/Header';
import { Card, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import api, { type Agent, type Task, type SystemHealth } from '@/lib/api';
import { useStore } from '@/store';

// Quick actions
const quickActions = [
  { label: 'Run Security Scan', icon: Shield, color: 'from-red-500 to-rose-600', action: 'scan_vulnerabilities', agent: 'security_agent' },
  { label: 'Sync Design Tokens', icon: Palette, color: 'from-violet-500 to-purple-600', action: 'sync_design_tokens', agent: 'design_agent' },
  { label: 'Deploy to Staging', icon: GitBranch, color: 'from-emerald-500 to-green-600', action: 'deploy', agent: 'deployment_agent' },
  { label: 'Generate Tests', icon: Zap, color: 'from-amber-500 to-orange-600', action: 'generate_tests', agent: 'testing_agent' },
];

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const variants: Record<string, 'success' | 'info' | 'warning' | 'error' | 'default'> = {
    completed: 'success',
    running: 'info',
    pending: 'default',
    failed: 'error',
    online: 'success',
    busy: 'warning',
    offline: 'default',
  };

  return (
    <Badge variant={variants[status] || 'default'} dot>
      {status}
    </Badge>
  );
};

export default function DashboardPage() {
  const [mounted, setMounted] = useState(false);
  const { tasks, agents: storeAgents, setTasks, setAgents } = useStore();

  // Fetch health/status
  const { data: healthData } = useSWR('/health', () => api.getHealth());
  const health = healthData?.data;

  // Fetch agents
  const { data: agentsData, mutate: mutateAgents } = useSWR('/api/v1/agents', () => api.getAgents(), {
    refreshInterval: 5000,
  });

  // Fetch recent tasks
  const { data: tasksData, mutate: mutateTasks } = useSWR('/api/v1/tasks', () => api.getTasks(10), {
    refreshInterval: 3000,
  });

  const handleQuickAction = async (action: typeof quickActions[0]) => {
    try {
      await api.execute(action.action, {});
      mutateTasks();
    } catch (error) {
      console.error('Failed to execute action:', error);
    }
  };

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (agentsData?.data) {
      setAgents(agentsData.data);
    }
  }, [agentsData, setAgents]);

  useEffect(() => {
    if (tasksData?.data) {
      setTasks(tasksData.data);
    }
  }, [tasksData, setTasks]);

  if (!mounted) return null;

  // Calculate stats from real data
  const activeTasks = tasks.filter(t => t.status === 'running' || t.status === 'pending').length;
  const completedTasks = tasks.filter(t => t.status === 'completed').length;
  const totalTasks = tasks.length;
  const successRate = totalTasks > 0 ? ((completedTasks / totalTasks) * 100).toFixed(1) : '0';
  
  const onlineAgents = storeAgents.filter(a => a.status === 'online').length;
  const totalAgents = storeAgents.length;

  const recentTasks = tasks.slice(0, 5);
  const topAgents = storeAgents.slice(0, 4);

  const stats = [
    {
      label: 'Active Tasks',
      value: String(activeTasks),
      change: '+12%',
      trend: 'up' as const,
      icon: Activity,
      color: 'primary',
    },
    {
      label: 'Agents Online',
      value: `${onlineAgents}/${totalAgents}`,
      change: totalAgents > 0 ? `${Math.round((onlineAgents / totalAgents) * 100)}%` : '0%',
      trend: 'up' as const,
      icon: Bot,
      color: 'emerald',
    },
    {
      label: 'Success Rate',
      value: `${successRate}%`,
      change: '+2.3%',
      trend: 'up' as const,
      icon: CheckCircle,
      color: 'blue',
    },
    {
      label: 'Avg Response',
      value: health?.uptime ? `${(health.uptime / 1000).toFixed(1)}s` : 'N/A',
      change: '-0.3s',
      trend: 'down' as const,
      icon: Clock,
      color: 'amber',
    },
  ];

  const agentIcons: Record<string, typeof Bot> = {
    'root_agent': Bot,
    'security_agent': Shield,
    'design_agent': Palette,
    'database_agent': Database,
    'testing_agent': Zap,
    'deployment_agent': GitBranch,
  };

  return (
    <>
      <Header title="Dashboard" description="Welcome back! Here's your DevOps overview." />

      <div className="p-8 space-y-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <Card variant="gradient" hover className="relative overflow-hidden">
                <div className={cn(
                  'absolute top-0 right-0 w-32 h-32 -mr-16 -mt-16 rounded-full opacity-20',
                  stat.color === 'primary' && 'bg-primary-500',
                  stat.color === 'emerald' && 'bg-emerald-500',
                  stat.color === 'blue' && 'bg-blue-500',
                  stat.color === 'amber' && 'bg-amber-500',
                )} />
                <div className="relative">
                  <div className="flex items-center justify-between mb-4">
                    <div className={cn(
                      'p-2 rounded-lg',
                      stat.color === 'primary' && 'bg-primary-500/20 text-primary-400',
                      stat.color === 'emerald' && 'bg-emerald-500/20 text-emerald-400',
                      stat.color === 'blue' && 'bg-blue-500/20 text-blue-400',
                      stat.color === 'amber' && 'bg-amber-500/20 text-amber-400',
                    )}>
                      <stat.icon className="w-5 h-5" />
                    </div>
                    <div className={cn(
                      'flex items-center gap-1 text-sm font-medium',
                      stat.trend === 'up' ? 'text-emerald-400' : 'text-red-400'
                    )}>
                      {stat.trend === 'up' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                      {stat.change}
                    </div>
                  </div>
                  <p className="text-sm text-slate-400 mb-1">{stat.label}</p>
                  <p className="text-3xl font-bold text-white">{stat.value}</p>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Tasks */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="lg:col-span-2"
          >
            <Card variant="default" padding="none">
              <div className="p-6 border-b border-slate-700/50">
                <CardTitle>Recent Tasks</CardTitle>
                <CardDescription>Latest activity across all agents</CardDescription>
              </div>
              <div className="divide-y divide-slate-700/50">
                {recentTasks.length > 0 ? (
                  recentTasks.map((task, i) => (
                    <motion.div
                      key={task.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.5 + i * 0.05 }}
                      className="px-6 py-4 hover:bg-slate-800/50 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-white truncate">{task.action || 'Task'}</p>
                          <p className="text-xs text-slate-400 mt-1">{task.agent} • {task.created_at ? new Date(task.created_at).toLocaleString() : 'N/A'}</p>
                        </div>
                        <StatusBadge status={task.status} />
                      </div>
                    </motion.div>
                  ))
                ) : (
                  <div className="px-6 py-8 text-center text-slate-400">
                    No recent tasks
                  </div>
                )}
              </div>
              <div className="p-4 border-t border-slate-700/50">
                <Button variant="ghost" className="w-full">
                  View All Tasks
                </Button>
              </div>
            </Card>
          </motion.div>

          {/* Agents Status */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <Card variant="elevated" padding="none">
              <div className="p-6 border-b border-slate-700/50">
                <CardTitle>Agent Status</CardTitle>
                <CardDescription>Real-time availability</CardDescription>
              </div>
              <div className="divide-y divide-slate-700/50">
                {topAgents.length > 0 ? (
                  topAgents.map((agent, i) => {
                    const Icon = agentIcons[agent.name] || Bot;
                    return (
                      <motion.div
                        key={agent.name}
                        initial={{ opacity: 0, x: 10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.6 + i * 0.05 }}
                        className="px-6 py-4 hover:bg-slate-800/50 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className={cn(
                              'w-2 h-2 rounded-full',
                              agent.status === 'online' && 'bg-emerald-400',
                              agent.status === 'busy' && 'bg-amber-400 animate-pulse',
                              agent.status === 'offline' && 'bg-slate-500',
                            )} />
                            <div>
                              <p className="text-sm font-medium text-white">{agent.name}</p>
                              <p className="text-xs text-slate-400">{agent.active_tasks || 0} tasks</p>
                            </div>
                          </div>
                          <StatusBadge status={agent.status} />
                        </div>
                      </motion.div>
                    );
                  })
                ) : (
                  <div className="px-6 py-8 text-center text-slate-400">
                    No agents available
                  </div>
                )}
              </div>
              <div className="p-4 border-t border-slate-700/50">
                <Button variant="ghost" className="w-full">
                  Manage Agents
                </Button>
              </div>
            </Card>
          </motion.div>
        </div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {quickActions.map((action, i) => (
              <motion.div
                key={action.label}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.8 + i * 0.05 }}
              >
                <Card
                  variant="glass"
                  hover
                  padding="md"
                  onClick={() => handleQuickAction(action)}
                  className="text-center cursor-pointer"
                >
                  <div className={cn(
                    'w-12 h-12 mx-auto mb-3 rounded-xl flex items-center justify-center',
                    'bg-gradient-to-br',
                    action.color
                  )}>
                    <action.icon className="w-6 h-6 text-white" />
                  </div>
                  <p className="text-sm font-medium text-slate-300">{action.label}</p>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </>
  );
}
