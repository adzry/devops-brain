'use client';

import { Sidebar } from '@/components/layout/Sidebar';
import { NewTaskModal } from '@/components/NewTaskModal';
import { useWebSocket } from '@/hooks/useWebSocket';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Initialize WebSocket connection
  useWebSocket();

  return (
    <div className="min-h-screen bg-background">
      {/* Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-primary-500/20 rounded-full blur-3xl opacity-50" />
        <div className="absolute top-1/2 -left-40 w-80 h-80 bg-secondary-500/15 rounded-full blur-3xl opacity-50" />
        <div className="absolute -bottom-40 right-1/3 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl opacity-50" />
        <div className="absolute inset-0 bg-grid opacity-50" />
      </div>

      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <main className="ml-64 relative">{children}</main>

      {/* Modals */}
      <NewTaskModal />
    </div>
  );
}
