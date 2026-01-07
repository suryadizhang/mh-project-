'use client';

import { ArrowLeft, Clock, Mail } from 'lucide-react';
import Link from 'next/link';
import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';

import { Button } from '@/components/ui/button';

// Inner component that uses useSearchParams (must be wrapped in Suspense)
function PendingApprovalContent() {
  const searchParams = useSearchParams();
  const email = searchParams.get('email') || 'your email';

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <div className="flex flex-col items-center space-y-6">
          {/* Icon */}
          <div className="h-16 w-16 bg-yellow-100 rounded-full flex items-center justify-center">
            <Clock className="h-8 w-8 text-yellow-600" />
          </div>

          {/* Heading */}
          <div className="text-center space-y-2">
            <h1 className="text-2xl font-bold text-gray-900">
              Account Pending Approval
            </h1>
            <p className="text-sm text-gray-600">
              Your account has been successfully created
            </p>
          </div>

          {/* Email Badge */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 w-full">
            <div className="flex items-center space-x-3">
              <Mail className="h-5 w-5 text-gray-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {email}
                </p>
                <p className="text-xs text-gray-500">Registered email</p>
              </div>
            </div>
          </div>

          {/* Information */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 w-full">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">
              What happens next?
            </h3>
            <ul className="space-y-2 text-sm text-blue-800">
              <li className="flex items-start">
                <span className="mr-2">•</span>
                <span>A system administrator will review your account</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">•</span>
                <span>
                  You&apos;ll receive an email notification once approved
                </span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">•</span>
                <span>This typically takes 1-2 business days</span>
              </li>
            </ul>
          </div>

          {/* Contact Support */}
          <div className="border-t border-gray-200 pt-6 w-full">
            <p className="text-sm text-gray-600 text-center mb-4">
              Need immediate access or have questions?
            </p>
            <Button
              variant="outline"
              className="w-full"
              onClick={() =>
                (window.location.href =
                  'mailto:support@myhibachi.com?subject=Account Approval Request')
              }
            >
              Contact Support
            </Button>
          </div>

          {/* Back to Login */}
          <Link
            href="/login"
            className="flex items-center text-sm text-blue-600 hover:text-blue-700"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to login
          </Link>
        </div>
      </div>
    </div>
  );
}

// Loading fallback for Suspense
function PendingApprovalFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading...</p>
      </div>
    </div>
  );
}

// Main exported component with Suspense boundary
export default function PendingApprovalPage() {
  return (
    <Suspense fallback={<PendingApprovalFallback />}>
      <PendingApprovalContent />
    </Suspense>
  );
}
