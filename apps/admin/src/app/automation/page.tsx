import { Metadata } from 'next';

import SEOAutomationDashboard from '@/components/SEOAutomationDashboard';

export const metadata: Metadata = {
  title: 'SEO Automation Dashboard | My Hibachi Admin',
  description:
    'Manage automated SEO and marketing tasks for My Hibachi locations',
  robots: 'noindex, nofollow',
};

export default function AutomationPage() {
  return <SEOAutomationDashboard />;
}
