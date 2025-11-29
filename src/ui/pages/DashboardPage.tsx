/**
 * DevOps Brain Dashboard Page
 * 
 * Main dashboard showcasing the design system with
 * beautiful, modern UI components.
 */

import React, { useState } from 'react';
import { Navbar } from '../components/Navbar';
import { Button } from '../components/Button';
import { Card, CardTitle, CardDescription, CardContent, CardFooter } from '../components/Card';
import { Input } from '../components/Input';
import { Modal } from '../components/Modal';

// Icons
const DashboardIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
  </svg>
);

const AgentsIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 00.659 1.591L19 14.5" />
  </svg>
);

const TasksIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
  </svg>
);

const DesignIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
  </svg>
);

const SearchIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
);

const TrendUpIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
  </svg>
);

const TrendDownIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
  </svg>
);

// Types
interface StatCardProps {
  title: string;
  value: string;
  change: string;
  trend: 'up' | 'down';
  icon: React.ReactNode;
}

interface AgentStatus {
  name: string;
  status: 'online' | 'busy' | 'offline';
  tasks: number;
  lastActive: string;
}

interface RecentTask {
  id: string;
  title: string;
  agent: string;
  status: 'completed' | 'running' | 'pending' | 'failed';
  time: string;
}

// Components
const StatCard: React.FC<StatCardProps> = ({ title, value, change, trend, icon }) => (
  <Card variant="gradient" hover className="relative overflow-hidden">
    <div className="absolute top-0 right-0 w-32 h-32 -mr-16 -mt-16 rounded-full bg-primary-500/10" />
    <div className="relative">
      <div className="flex items-center justify-between mb-4">
        <div className="p-2 rounded-lg bg-primary-500/20 text-primary-400">
          {icon}
        </div>
        <div className={`flex items-center gap-1 text-sm font-medium ${
          trend === 'up' ? 'text-emerald-400' : 'text-red-400'
        }`}>
          {trend === 'up' ? <TrendUpIcon /> : <TrendDownIcon />}
          {change}
        </div>
      </div>
      <p className="text-sm text-slate-400 mb-1">{title}</p>
      <p className="text-3xl font-bold text-white">{value}</p>
    </div>
  </Card>
);

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const styles = {
    online: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    busy: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    offline: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
    completed: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    running: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    pending: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
    failed: 'bg-red-500/20 text-red-400 border-red-500/30',
  };
  
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${styles[status as keyof typeof styles] || styles.offline}`}>
      {status}
    </span>
  );
};

// Main Dashboard Component
export const DashboardPage: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const stats: StatCardProps[] = [
    { title: 'Active Tasks', value: '24', change: '+12%', trend: 'up', icon: <TasksIcon /> },
    { title: 'Agents Online', value: '10', change: '0%', trend: 'up', icon: <AgentsIcon /> },
    { title: 'Success Rate', value: '98.5%', change: '+2.3%', trend: 'up', icon: <DashboardIcon /> },
    { title: 'Avg Response', value: '1.2s', change: '-0.3s', trend: 'down', icon: <DesignIcon /> },
  ];

  const agents: AgentStatus[] = [
    { name: 'Root Agent', status: 'online', tasks: 3, lastActive: 'Now' },
    { name: 'Security Agent', status: 'busy', tasks: 2, lastActive: '2m ago' },
    { name: 'Design Agent', status: 'online', tasks: 0, lastActive: '5m ago' },
    { name: 'Testing Agent', status: 'online', tasks: 1, lastActive: '1m ago' },
    { name: 'Deploy Agent', status: 'offline', tasks: 0, lastActive: '1h ago' },
  ];

  const recentTasks: RecentTask[] = [
    { id: 'task-1', title: 'Security vulnerability scan', agent: 'Security Agent', status: 'completed', time: '2 min ago' },
    { id: 'task-2', title: 'Generate UI components from Figma', agent: 'Design Agent', status: 'running', time: '5 min ago' },
    { id: 'task-3', title: 'Run test suite', agent: 'Testing Agent', status: 'pending', time: '10 min ago' },
    { id: 'task-4', title: 'Deploy to staging', agent: 'Deploy Agent', status: 'completed', time: '15 min ago' },
    { id: 'task-5', title: 'Code review PR #142', agent: 'Code Review Agent', status: 'completed', time: '20 min ago' },
  ];

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-primary-500/20 rounded-full blur-3xl animate-pulse-glow" />
        <div className="absolute top-1/2 -left-40 w-80 h-80 bg-secondary-500/15 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 right-1/3 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl" />
        {/* Grid Pattern */}
        <div 
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `linear-gradient(rgba(99, 102, 241, 0.3) 1px, transparent 1px),
                            linear-gradient(90deg, rgba(99, 102, 241, 0.3) 1px, transparent 1px)`,
            backgroundSize: '50px 50px',
          }}
        />
      </div>

      {/* Navbar */}
      <Navbar
        items={[
          { label: 'Dashboard', href: '/dashboard', icon: <DashboardIcon />, active: true },
          { label: 'Agents', href: '/agents', icon: <AgentsIcon /> },
          { label: 'Tasks', href: '/tasks', icon: <TasksIcon /> },
          { label: 'Design', href: '/design', icon: <DesignIcon /> },
        ]}
        actions={
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm">
              Docs
            </Button>
            <Button variant="primary" size="sm" onClick={() => setIsModalOpen(true)}>
              New Task
            </Button>
          </div>
        }
      />

      {/* Main Content */}
      <main className="relative pt-24 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">
              Welcome back, <span className="text-gradient-primary">Developer</span>
            </h1>
            <p className="text-slate-400">
              Here's what's happening with your DevOps Brain today.
            </p>
          </div>
          <div className="w-full md:w-72">
            <Input
              placeholder="Search tasks, agents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              iconLeft={<SearchIcon />}
            />
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, i) => (
            <div key={i} className="animate-fade-in" style={{ animationDelay: `${i * 100}ms` }}>
              <StatCard {...stat} />
            </div>
          ))}
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Activity */}
          <Card variant="default" padding="none" className="lg:col-span-2">
            <div className="p-6 border-b border-slate-700/50">
              <CardTitle>Recent Tasks</CardTitle>
              <CardDescription>Latest activity across all agents</CardDescription>
            </div>
            <div className="divide-y divide-slate-700/50">
              {recentTasks.map((task, i) => (
                <div
                  key={task.id}
                  className="px-6 py-4 hover:bg-slate-800/50 transition-colors animate-slide-up"
                  style={{ animationDelay: `${i * 50}ms` }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">
                        {task.title}
                      </p>
                      <p className="text-xs text-slate-400 mt-1">
                        {task.agent} • {task.time}
                      </p>
                    </div>
                    <StatusBadge status={task.status} />
                  </div>
                </div>
              ))}
            </div>
            <div className="p-4 border-t border-slate-700/50">
              <Button variant="ghost" fullWidth>
                View All Tasks
              </Button>
            </div>
          </Card>

          {/* Agents Status */}
          <Card variant="elevated" padding="none">
            <div className="p-6 border-b border-slate-700/50">
              <CardTitle>Agent Status</CardTitle>
              <CardDescription>Real-time agent availability</CardDescription>
            </div>
            <div className="divide-y divide-slate-700/50">
              {agents.map((agent, i) => (
                <div
                  key={agent.name}
                  className="px-6 py-4 hover:bg-slate-800/50 transition-colors animate-slide-up"
                  style={{ animationDelay: `${i * 50}ms` }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${
                        agent.status === 'online' ? 'bg-emerald-400' :
                        agent.status === 'busy' ? 'bg-amber-400 animate-pulse' :
                        'bg-slate-500'
                      }`} />
                      <div>
                        <p className="text-sm font-medium text-white">
                          {agent.name}
                        </p>
                        <p className="text-xs text-slate-400">
                          {agent.tasks} tasks • {agent.lastActive}
                        </p>
                      </div>
                    </div>
                    <StatusBadge status={agent.status} />
                  </div>
                </div>
              ))}
            </div>
            <div className="p-4 border-t border-slate-700/50">
              <Button variant="ghost" fullWidth>
                Manage Agents
              </Button>
            </div>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Run Security Scan', icon: '🔒' },
              { label: 'Sync Design Tokens', icon: '🎨' },
              { label: 'Deploy to Staging', icon: '🚀' },
              { label: 'Generate Tests', icon: '🧪' },
            ].map((action, i) => (
              <Card
                key={i}
                variant="glass"
                hover
                padding="md"
                onClick={() => console.log(`Execute: ${action.label}`)}
                className="text-center"
              >
                <div className="text-3xl mb-2">{action.icon}</div>
                <p className="text-sm font-medium text-slate-300">{action.label}</p>
              </Card>
            ))}
          </div>
        </div>
      </main>

      {/* New Task Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create New Task"
        description="Assign a task to an AI agent"
        size="md"
        footer={
          <>
            <Button variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={() => setIsModalOpen(false)}>
              Create Task
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="Task Title"
            placeholder="e.g., Run security audit on main branch"
          />
          <Input
            label="Description"
            placeholder="Describe what the agent should do..."
          />
          <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700">
            <p className="text-sm text-slate-400 mb-2">Agent will be auto-assigned based on task type</p>
            <p className="text-xs text-slate-500">
              Tip: Use keywords like "security", "design", "test" to route to specific agents
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default DashboardPage;
