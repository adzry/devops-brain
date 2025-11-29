'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import useSWR from 'swr';
import {
  ListTodo,
  Play,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  Filter,
  Search,
  ChevronDown,
  MoreHorizontal,
  RefreshCw,
  Trash2,
  Eye,
} from 'lucide-react';
import { Header } from '@/components/layout/Header';
import { Card, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { cn, formatRelativeTime } from '@/lib/utils';
import api, { type Task } from '@/lib/api';
import { useStore } from '@/store';

// Fallback mock data for development
const mockTasks: Task[] = [
  {
    id: 'task-001',
    action: 'Security vulnerability scan on main branch',
    agent: 'Security Agent',
    status: 'completed',
    created_at: new Date(Date.now() - 120000).toISOString(),
    completed_at: new Date(Date.now() - 60000).toISOString(),
    result: { vulnerabilities_found: 3, critical: 0, high: 1, medium: 2 },
  },
  {
    id: 'task-002',
    action: 'Generate React components from Figma design',
    agent: 'Design Agent',
    status: 'running',
    created_at: new Date(Date.now() - 300000).toISOString(),
  },
  {
    id: 'task-003',
    action: 'Run test suite with coverage analysis',
    agent: 'Testing Agent',
    status: 'pending',
    created_at: new Date(Date.now() - 600000).toISOString(),
  },
  {
    id: 'task-004',
    action: 'Deploy application to staging environment',
    agent: 'Deployment Agent',
    status: 'completed',
    created_at: new Date(Date.now() - 900000).toISOString(),
    completed_at: new Date(Date.now() - 850000).toISOString(),
    result: { environment: 'staging', version: 'v1.2.3' },
  },
  {
    id: 'task-005',
    action: 'Code review for PR #142',
    agent: 'Code Review Agent',
    status: 'completed',
    created_at: new Date(Date.now() - 1200000).toISOString(),
    completed_at: new Date(Date.now() - 1100000).toISOString(),
    result: { issues: 2, suggestions: 5, approved: true },
  },
  {
    id: 'task-006',
    action: 'Database migration v45',
    agent: 'Database Agent',
    status: 'failed',
    created_at: new Date(Date.now() - 1800000).toISOString(),
    completed_at: new Date(Date.now() - 1700000).toISOString(),
    error: 'Foreign key constraint violation',
  },
  {
    id: 'task-007',
    action: 'Performance profiling for API endpoints',
    agent: 'Performance Agent',
    status: 'completed',
    created_at: new Date(Date.now() - 3600000).toISOString(),
    completed_at: new Date(Date.now() - 3500000).toISOString(),
    result: { bottlenecks: 2, p99_latency: '245ms' },
  },
] as Task[];

const statusConfig = {
  completed: { icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/20', variant: 'success' as const },
  running: { icon: Loader2, color: 'text-blue-400', bg: 'bg-blue-500/20', variant: 'info' as const },
  pending: { icon: Clock, color: 'text-slate-400', bg: 'bg-slate-500/20', variant: 'default' as const },
  failed: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/20', variant: 'error' as const },
};

export default function TasksPage() {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [filter, setFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const { tasks: storeTasks, setTasks } = useStore();

  // Fetch tasks from API
  const { data: tasksResponse, error, mutate } = useSWR(
    '/api/v1/tasks?limit=100',
    async () => {
      const response = await api.getTasks(100);
      if (response.error) {
        console.error('Failed to fetch tasks:', response.error);
        return { tasks: mockTasks };
      }
      // API returns { tasks: [...], total: number }
      const apiTasks = response.data?.tasks || [];
      // Map API task format to frontend Task format
      const mappedTasks: Task[] = apiTasks.map((t: any) => ({
        id: t.task_id,
        action: t.action,
        agent: t.agent,
        status: t.status,
        created_at: t.created_at || new Date().toISOString(),
        completed_at: t.completed_at,
        result: t.result,
        error: t.error,
      }));
      return { tasks: mappedTasks.length > 0 ? mappedTasks : mockTasks };
    },
    {
      refreshInterval: 5000, // Refresh every 5 seconds
      revalidateOnFocus: true,
    }
  );

  // Update store when tasks are fetched
  useEffect(() => {
    if (tasksResponse?.tasks) {
      setTasks(tasksResponse.tasks);
    }
  }, [tasksResponse, setTasks]);

  // Use store tasks or fallback to mock
  const tasks = storeTasks.length > 0 ? storeTasks : (tasksResponse?.tasks || mockTasks);

  const filteredTasks = tasks.filter((task) => {
    if (filter !== 'all' && task.status !== filter) return false;
    const searchText = task.action || '';
    if (searchQuery && !searchText.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const taskCounts = {
    all: tasks.length,
    completed: tasks.filter(t => t.status === 'completed').length,
    running: tasks.filter(t => t.status === 'running').length,
    pending: tasks.filter(t => t.status === 'pending').length,
    failed: tasks.filter(t => t.status === 'failed').length,
  };

  const handleRefresh = () => {
    mutate();
  };

  return (
    <>
      <Header title="Tasks" description="Monitor and manage task executions" />

      <div className="p-8">
        {/* Filters */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            {(['all', 'running', 'pending', 'completed', 'failed'] as const).map((status) => (
              <button
                key={status}
                onClick={() => setFilter(status)}
                className={cn(
                  'px-4 py-2 rounded-xl text-sm font-medium transition-all',
                  filter === status
                    ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                )}
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
                <span className="ml-2 text-xs opacity-60">({taskCounts[status]})</span>
              </button>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <div className="w-64">
              <Input
                placeholder="Search tasks..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                icon={<Search className="w-4 h-4" />}
                className="py-2"
              />
            </div>
            <Button variant="secondary" size="sm" icon={<RefreshCw className="w-4 h-4" />} onClick={handleRefresh}>
              Refresh
            </Button>
          </div>
        </div>

        {/* Tasks List */}
        <Card variant="default" padding="none">
          {/* Header */}
          <div className="grid grid-cols-12 gap-4 px-6 py-3 border-b border-slate-700/50 text-xs font-medium text-slate-500 uppercase tracking-wider">
            <div className="col-span-5">Task</div>
            <div className="col-span-2">Agent</div>
            <div className="col-span-2">Status</div>
            <div className="col-span-2">Time</div>
            <div className="col-span-1"></div>
          </div>

          {/* Tasks */}
          <div className="divide-y divide-slate-700/50">
            <AnimatePresence>
              {filteredTasks.map((task, i) => {
                const config = statusConfig[task.status as keyof typeof statusConfig];
                const StatusIcon = config.icon;

                return (
                  <motion.div
                    key={task.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ delay: i * 0.03 }}
                    className="grid grid-cols-12 gap-4 px-6 py-4 items-center hover:bg-slate-800/50 transition-colors group"
                  >
                    {/* Task Info */}
                    <div className="col-span-5 flex items-center gap-3">
                      <div className={cn('p-2 rounded-lg', config.bg)}>
                        <StatusIcon className={cn('w-4 h-4', config.color, task.status === 'running' && 'animate-spin')} />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-white truncate">{task.action}</p>
                        <p className="text-xs text-slate-500">{task.id}</p>
                      </div>
                    </div>

                    {/* Agent */}
                    <div className="col-span-2">
                      <span className="text-sm text-slate-400">{task.agent}</span>
                    </div>

                    {/* Status */}
                    <div className="col-span-2">
                      <Badge variant={config.variant} dot>
                        {task.status}
                        {task.status === 'running' && task.progress && (
                          <span className="ml-1">({task.progress}%)</span>
                        )}
                      </Badge>
                    </div>

                    {/* Time */}
                    <div className="col-span-2">
                      <p className="text-sm text-slate-400">{formatRelativeTime(task.created_at)}</p>
                      {task.completed_at && task.created_at && (
                        <p className="text-xs text-slate-500">
                          Duration: {Math.round((new Date(task.completed_at).getTime() - new Date(task.created_at).getTime()) / 1000)}s
                        </p>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="col-span-1 flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => setSelectedTask(task)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      {task.status === 'failed' && (
                        <button className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition-colors">
                          <RefreshCw className="w-4 h-4" />
                        </button>
                      )}
                      <button className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-700 transition-colors">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>

          {/* Empty State */}
          {filteredTasks.length === 0 && (
            <div className="px-6 py-12 text-center">
              <ListTodo className="w-12 h-12 mx-auto text-slate-600 mb-4" />
              <p className="text-slate-400">No tasks found</p>
            </div>
          )}
        </Card>
      </div>

      {/* Task Detail Modal */}
      <Modal
        isOpen={!!selectedTask}
        onClose={() => setSelectedTask(null)}
        title={selectedTask?.action}
        description={`Task ID: ${selectedTask?.id}`}
        size="lg"
      >
        {selectedTask && (
          <div className="space-y-6">
            {/* Status & Agent */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Status</p>
                <Badge variant={statusConfig[selectedTask.status as keyof typeof statusConfig].variant} dot>
                  {selectedTask.status}
                </Badge>
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Agent</p>
                <p className="text-sm text-white">{selectedTask.agent}</p>
              </div>
            </div>

            {/* Timestamps */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Created</p>
                <p className="text-sm text-white">{new Date(selectedTask.created_at).toLocaleString()}</p>
              </div>
              {selectedTask.completed_at && (
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Completed</p>
                  <p className="text-sm text-white">{new Date(selectedTask.completed_at).toLocaleString()}</p>
                </div>
              )}
            </div>

            {/* Result or Error */}
            {selectedTask.result && (
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Result</p>
                <pre className="p-4 rounded-xl bg-slate-800 text-sm text-slate-300 overflow-auto">
                  {JSON.stringify(selectedTask.result, null, 2)}
                </pre>
              </div>
            )}

            {selectedTask.error && (
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Error</p>
                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-sm text-red-400">
                  {selectedTask.error}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </>
  );
}
