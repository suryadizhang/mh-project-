import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Contact - My Hibachi Chef',
  description: 'Contact My Hibachi Chef for your next event',
};

export default function ContactHtmlLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
