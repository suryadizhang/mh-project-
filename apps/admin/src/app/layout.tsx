import type { Metadata } from 'next';
import './globals.css';
import AdminLayoutComponent from './AdminLayoutComponent';
import { AuthProvider } from '@/contexts/AuthContext';
import { ToastProvider } from '@/components/ui/Toast';

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
