'use client';

import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';

import { getContactData } from '@/lib/contactData';

declare global {
  interface Window {
    FB?: {
      init: (config: { xfbml: boolean; version: string }) => void;
      CustomerChat: {
        show: () => void;
        hide: () => void;
      };
    };
    fbAsyncInit?: () => void;
  }
}

export default function MetaMessenger() {
  const pathname = usePathname();
  const onContact = pathname === '/contact';
  const [hasConsent, setHasConsent] = useState(false);
  const [sdkLoaded, setSdkLoaded] = useState(false);

  useEffect(() => {
    if (!onContact) return;

    const checkConsent = () => {
      const consent = localStorage.getItem('mh_consent');
      setHasConsent(consent === 'true');
    };

    checkConsent();

    // Listen for consent changes
    const handleConsentGranted = () => {
      checkConsent();
    };

    window.addEventListener('consentGranted', handleConsentGranted);

    // Also check periodically in case consent changes
    const interval = setInterval(checkConsent, 1000);

    return () => {
      window.removeEventListener('consentGranted', handleConsentGranted);
      clearInterval(interval);
    };
  }, [onContact]);

  useEffect(() => {
    if (!onContact || !hasConsent || sdkLoaded) return;

    const { pageId, appId } = getContactData();

    if (!pageId || !appId) {
      console.warn('Facebook Page ID or App ID not configured');
      return;
    }

    // Initialize Facebook SDK
    window.fbAsyncInit = function () {
      if (window.FB) {
        window.FB.init({
          xfbml: true,
          version: 'v18.0',
        });
      }
      setSdkLoaded(true);
    };

    // Load Facebook SDK
    const script = document.createElement('script');
    script.async = true;
    script.defer = true;
    script.crossOrigin = 'anonymous';
    script.src = `https://connect.facebook.net/en_US/sdk/xfbml.customerchat.js#xfbml=1&version=v18.0&autoLogAppEvents=1&appId=${appId}`;
    script.id = 'facebook-jssdk';

    if (!document.getElementById('facebook-jssdk')) {
      document.head.appendChild(script);
    }

    return () => {
      // Cleanup if needed
      const existingScript = document.getElementById('facebook-jssdk');
      if (existingScript) {
        existingScript.remove();
      }
    };
  }, [onContact, hasConsent, sdkLoaded]);

  if (!onContact || !hasConsent) return null;

  const { pageId, greetings } = getContactData();

  if (!pageId) return null;

  return (
    <div
      id="fb-customer-chat"
      className="fb-customerchat"
      data-page-id={pageId}
      data-attribution="biz_inbox"
      data-greeting-dialog-display="hide"
      data-logged-in-greeting={greetings.loggedIn}
      data-logged-out-greeting={greetings.loggedOut}
      data-theme-color="#DB2B28"
    />
  );
}
