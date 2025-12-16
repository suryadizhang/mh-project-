import {
  AlertTriangle,
  BookText,
  Calculator,
  CalendarCheck,
  Home,
  Menu,
  Phone,
} from 'lucide-react';
import Link from 'next/link';

import Breadcrumb from '@/components/ui/Breadcrumb';
import { ProtectedPhone } from '@/components/ui/ProtectedPhone';
import { generatePageMetadata } from '@/lib/seo-config';

export const metadata = generatePageMetadata({
  title: 'Page Not Found - 404 Error',
  description:
    "The page you're looking for doesn't exist. Return to My Hibachi Chef homepage or explore our hibachi catering services.",
  noIndex: true,
});

export default function NotFound() {
  const breadcrumbItems = [
    { label: 'Home', href: '/' },
    { label: '404 Error', href: '/404' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4">
        <Breadcrumb items={breadcrumbItems} className="pt-4" />

        <div className="flex min-h-[80vh] flex-col items-center justify-center text-center">
          {/* 404 Visual */}
          <div className="mb-8">
            <div className="mb-4 bg-gradient-to-r from-orange-400 to-red-500 bg-clip-text text-8xl font-bold text-transparent md:text-9xl">
              404
            </div>
            <div className="mb-6 flex justify-center">
              <AlertTriangle className="h-16 w-16 text-orange-400" />
            </div>
          </div>

          {/* Error Message */}
          <div className="mb-8 max-w-2xl">
            <h1 className="mb-4 text-3xl font-bold text-white md:text-4xl">Oops! Page Not Found</h1>
            <p className="mb-6 text-lg text-gray-300">
              The page you&apos;re looking for seems to have vanished like sizzling hibachi steam!
              Don&apos;t worry, let&apos;s get you back to the delicious action.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="mb-8 flex flex-col gap-4 sm:flex-row">
            <Link
              href="/"
              className="inline-flex transform items-center rounded-lg bg-gradient-to-r from-orange-500 to-red-500 px-8 py-4 font-semibold text-white transition-all duration-300 hover:scale-105 hover:from-orange-600 hover:to-red-600 hover:shadow-lg"
            >
              <Home className="mr-2 h-5 w-5" />
              Back to Home
            </Link>

            <Link
              href="/BookUs"
              className="inline-flex transform items-center rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 px-8 py-4 font-semibold text-white transition-all duration-300 hover:scale-105 hover:from-blue-600 hover:to-purple-600 hover:shadow-lg"
            >
              <CalendarCheck className="mr-2 h-5 w-5" />
              Book Hibachi
            </Link>
          </div>

          {/* Helpful Links */}
          <div className="grid max-w-4xl grid-cols-2 gap-4 md:grid-cols-4">
            <Link
              href="/menu"
              className="group rounded-lg bg-slate-800/50 p-4 text-center transition-colors hover:bg-slate-700/50"
            >
              <Menu className="mx-auto mb-2 h-8 w-8 text-orange-400 group-hover:text-orange-300" />
              <span className="text-sm text-white">Menu</span>
            </Link>

            <Link
              href="/quote"
              className="group rounded-lg bg-slate-800/50 p-4 text-center transition-colors hover:bg-slate-700/50"
            >
              <Calculator className="mx-auto mb-2 h-8 w-8 text-orange-400 group-hover:text-orange-300" />
              <span className="text-sm text-white">Get Quote</span>
            </Link>

            <Link
              href="/blog"
              className="group rounded-lg bg-slate-800/50 p-4 text-center transition-colors hover:bg-slate-700/50"
            >
              <BookText className="mx-auto mb-2 h-8 w-8 text-orange-400 group-hover:text-orange-300" />
              <span className="text-sm text-white">Blog</span>
            </Link>

            <Link
              href="/contact"
              className="group rounded-lg bg-slate-800/50 p-4 text-center transition-colors hover:bg-slate-700/50"
            >
              <Phone className="mx-auto mb-2 h-8 w-8 text-orange-400 group-hover:text-orange-300" />
              <span className="text-sm text-white">Contact</span>
            </Link>
          </div>

          {/* Contact Info */}
          <div className="mt-8 text-center">
            <p className="mb-2 text-gray-400">Need immediate assistance?</p>
            <ProtectedPhone
              className="text-lg font-semibold text-orange-400 hover:text-orange-300"
              showIcon={true}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
