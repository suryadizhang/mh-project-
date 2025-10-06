import type { Metadata } from 'next';
import './globals.css';
import AdminLayoutComponent from './AdminLayoutComponent';
import { AuthProvider } from '@/contexts/AuthContext';

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
    <html lang="en">
      <body suppressHydrationWarning>
        <AuthProvider>
          <AdminLayoutComponent>{children}</AdminLayoutComponent>
        </AuthProvider>
      </body>
    </html>
  );
}
