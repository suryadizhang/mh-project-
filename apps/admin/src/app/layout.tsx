import './globals.css';

import type { Metadata } from 'next';

import { ToastProvider } from '@/components/ui/Toast';
import { AuthProvider } from '@/contexts/AuthContext';

import AdminLayoutComponent from './AdminLayoutComponent';

export const metadata: Metadata = {
  title: 'MyHibachi Admin Dashboard',
  description: 'Administrative dashboard for MyHibachi catering management',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <AuthProvider>
          <ToastProvider>
            <AdminLayoutComponent>{children}</AdminLayoutComponent>
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
