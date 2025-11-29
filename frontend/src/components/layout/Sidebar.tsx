'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Bot,
  ListTodo,
  Palette,
  Settings,
  Activity,
  Shield,
  Database,
  Cloud,
  FileCode,
  Brain,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Agents', href: '/agents', icon: Bot },
  { name: 'Tasks', href: '/tasks', icon: ListTodo },
  { name: 'Workflows', href: '/workflows', icon: Activity },
  { name: 'Design', href: '/design', icon: Palette },
];

const agents = [
  { name: 'Security', icon: Shield, status: 'online' },
  { name: 'Database', icon: Database, status: 'online' },
  { name: 'Infrastructure', icon: Cloud, status: 'busy' },
  { name: 'Testing', icon: FileCode, status: 'online' },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-slate-900/50 backdrop-blur-xl border-r border-slate-800 z-40">
      <div className="flex flex-col h-full">
        {/* Logo */}
        <div className="p-6">
          <Link href="/dashboard" className="flex items-center gap-3 group">
            <div className="p-2 rounded-xl bg-primary-500/20 text-primary-400 group-hover:bg-primary-500/30 transition-colors">
              <Brain className="w-6 h-6" />
            </div>
            <span className="text-xl font-bold text-gradient">DevOps Brain</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 space-y-1">
          <p className="px-3 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Main
          </p>
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                )}
              >
                <item.icon className="w-5 h-5" />
                {item.name}
                {isActive && (
                  <motion.div
                    layoutId="sidebar-indicator"
                    className="ml-auto w-1.5 h-1.5 rounded-full bg-primary-400"
                  />
                )}
              </Link>
            );
          })}

          {/* Agents Section */}
          <p className="px-3 py-2 mt-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Active Agents
          </p>
          {agents.map((agent) => (
            <div
              key={agent.name}
              className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-slate-400"
            >
              <agent.icon className="w-4 h-4" />
              <span>{agent.name}</span>
              <span
                className={cn(
                  'ml-auto w-2 h-2 rounded-full',
                  agent.status === 'online' && 'bg-emerald-400',
                  agent.status === 'busy' && 'bg-amber-400 animate-pulse',
                  agent.status === 'offline' && 'bg-slate-500'
                )}
              />
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800">
          <Link
            href="/settings"
            className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <Settings className="w-5 h-5" />
            Settings
          </Link>
          <div className="flex items-center gap-2 px-3 py-2 mt-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <span className="text-xs text-slate-500">System Online</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
