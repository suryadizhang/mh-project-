import nextDynamic from 'next/dynamic'
import MenuHero from '@/components/menu/MenuHero'
import PricingSection from '@/components/menu/PricingSection'
import '@/styles/menu/base.css'
import Assistant from '@/components/chat/Assistant'

// Dynamic imports for below-the-fold sections
const ProteinsSection = nextDynamic(() => import('@/components/menu/ProteinsSection'), { 
  ssr: false,
  loading: () => <div className="text-center p-4">Loading proteins...</div>
})

const AdditionalSection = nextDynamic(() => import('@/components/menu/AdditionalSection'), { 
  ssr: false,
  loading: () => <div className="text-center p-4">Loading additional services...</div>
})

const ServiceAreas = nextDynamic(() => import('@/components/menu/ServiceAreas'), { 
  ssr: false,
  loading: () => <div className="text-center p-4">Loading service areas...</div>
})

const CTASection = nextDynamic(() => import('@/components/menu/CTASection'), { 
  ssr: false,
  loading: () => <div className="text-center p-4">Loading...</div>
})

// Force static generation for better performance
export const dynamic = 'force-static'
export const revalidate = 3600 // Revalidate every hour

export default function MenuPage() {
  return (
    <main>
      {/* Menu Container */}
      <div className="menu-container">
        <div className="container-fluid px-lg-5">
          {/* Above-the-fold content - rendered immediately */}
          <MenuHero />
          <PricingSection />
          
          {/* Below-the-fold content - loaded dynamically */}
          <ProteinsSection />
          <AdditionalSection />
          <ServiceAreas />
          <CTASection />
          
          {/* Assistant component */}
          <Assistant />
        </div>
      </div>
    </main>
  )
}
