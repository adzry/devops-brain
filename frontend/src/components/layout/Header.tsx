'use client';

import React from 'react';
import { Bell, Search, Plus } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useStore } from '@/store';

interface HeaderProps {
  title: string;
  description?: string;
}

export const Header: React.FC<HeaderProps> = ({ title, description }) => {
  const openModal = useStore((state) => state.openModal);

  return (
    <header className="sticky top-0 z-30 bg-background/80 backdrop-blur-xl border-b border-slate-800">
      <div className="flex items-center justify-between px-8 py-4">
        {/* Title */}
        <div>
          <h1 className="text-2xl font-bold text-white">{title}</h1>
          {description && <p className="text-sm text-slate-400 mt-1">{description}</p>}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="w-64">
            <Input
              placeholder="Search..."
              icon={<Search className="w-4 h-4" />}
              className="py-2"
            />
          </div>

          {/* Notifications */}
          <button className="relative p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-primary-500 rounded-full" />
          </button>

          {/* New Task Button */}
          <Button
            size="sm"
            icon={<Plus className="w-4 h-4" />}
            onClick={() => openModal('new-task')}
          >
            New Task
          </Button>
        </div>
      </div>
    </header>
  );
};
