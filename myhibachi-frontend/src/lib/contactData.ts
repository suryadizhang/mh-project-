import contact from '@/data/contact.json'

export function getContactData() {
  return {
    pageId: contact.facebookPageId || process.env.NEXT_PUBLIC_FB_PAGE_ID || '',
    appId: contact.facebookAppId || process.env.NEXT_PUBLIC_FB_APP_ID || '',
    igUser: contact.instagramUsername || process.env.NEXT_PUBLIC_IG_USERNAME || '',
    igUrl: contact.instagramDmUrl || (contact.instagramUsername ? `https://ig.me/m/${contact.instagramUsername}` : ''),
    phone: contact.phone || '',
    email: contact.email || '',
    greetings: contact.greetings || {
      loggedIn: 'Hi! How can we help with your hibachi booking?',
      loggedOut: 'Hi! How can we help with your hibachi booking?'
    }
  }
}

export function openIG(igUser: string, igDmUrl: string) {
  const app = `instagram://user?username=${igUser}`
  if (/Android|iPhone/i.test(navigator.userAgent)) {
    window.location.href = app
    setTimeout(() => window.open(igDmUrl || `https://ig.me/m/${igUser}`, '_blank'), 400)
  } else {
    window.open(igDmUrl || `https://ig.me/m/${igUser}`, '_blank')
  }

  // GTM tracking
  if (typeof window !== 'undefined' && (window as unknown as { dataLayer?: unknown[] }).dataLayer) {
    ;(window as unknown as { dataLayer: unknown[] }).dataLayer.push({ event: 'chat_open', channel: 'instagram' })
  }
}
