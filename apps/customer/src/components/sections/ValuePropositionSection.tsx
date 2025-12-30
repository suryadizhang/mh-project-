'use client';

import {
  ArrowRight,
  Calendar,
  Check,
  ChefHat,
  Clock,
  Crown,
  MapPin,
  Phone,
  Plus,
  Sparkles,
  Star,
  Users,
  Utensils,
  X,
  Zap,
} from 'lucide-react';
import Link from 'next/link';

import { useAnalytics } from '@/components/analytics/GoogleAnalytics';
import { usePricing } from '@/hooks/usePricing';

/**
 * Value Proposition + Urgency Section
 *
 * Replaces fake testimonials with real value-driven content:
 * - Why Choose My Hibachi Chef
 * - What's Included vs Restaurant
 * - Urgency/CTA with real booking info
 *
 * All data is real - no fake reviews or made-up statistics.
 */

interface IncludedItem {
  icon: React.ReactNode;
  title: string;
  description: string;
  highlight?: string;
}

interface ComparisonItem {
  feature: string;
  hibachi: string;
  restaurant: string;
  hibachiWins: boolean;
}

const includedItems: IncludedItem[] = [
  {
    icon: <Utensils className="h-5 w-5" />,
    title: '2 Proteins Per Guest',
    description: 'Chicken, NY Strip Steak, Shrimp, Calamari, or Tofu',
    highlight: 'Your choice',
  },
  {
    icon: <Sparkles className="h-5 w-5" />,
    title: 'Premium Sides',
    description: 'Hibachi fried rice, fresh vegetables, side salad & signature sauces',
  },
  {
    icon: <ChefHat className="h-5 w-5" />,
    title: 'Live Entertainment',
    description: 'Professional chef performs exciting hibachi show at your event',
  },
  {
    icon: <Star className="h-5 w-5" />,
    title: 'Complimentary Sake',
    description: 'Traditional sake service for guests 21+ included',
  },
];

const upgradeItems = [
  {
    title: 'Premium Proteins',
    items: [
      { name: 'Salmon', price: '+$5' },
      { name: 'Scallops', price: '+$5' },
      { name: 'Filet Mignon', price: '+$5' },
      { name: 'Extra Protein', price: '+$10' },
    ],
    note: 'per order',
    icon: <Crown className="h-5 w-5" />,
  },
  {
    title: 'Lobster Tail',
    items: [{ name: 'Fresh lobster tail upgrade', price: '+$15' }],
    note: 'per order',
    icon: <Star className="h-5 w-5" />,
  },
  {
    title: 'Sides & Extras',
    items: [
      { name: 'Yakisoba Noodles', price: '+$5' },
      { name: 'Extra Rice', price: '+$5' },
      { name: 'Extra Vegetables', price: '+$5' },
    ],
    note: 'per order',
    icon: <Plus className="h-5 w-5" />,
  },
  {
    title: 'Appetizers',
    items: [
      { name: 'Gyoza (Dumplings)', price: '+$10' },
      { name: 'Edamame', price: '+$5' },
    ],
    note: 'per order',
    icon: <Utensils className="h-5 w-5" />,
  },
];

const comparisonItems: ComparisonItem[] = [
  {
    feature: 'Location',
    hibachi: 'Your backyard, home, or venue',
    restaurant: 'Fixed restaurant location',
    hibachiWins: true,
  },
  {
    feature: 'Privacy',
    hibachi: 'Private event, just your guests',
    restaurant: 'Shared with strangers',
    hibachiWins: true,
  },
  {
    feature: 'Flexibility',
    hibachi: 'Your schedule, your menu',
    restaurant: 'Limited hours & fixed menu',
    hibachiWins: true,
  },
  {
    feature: 'Experience',
    hibachi: 'Chef cooks exclusively for you',
    restaurant: 'Chef splits attention',
    hibachiWins: true,
  },
  {
    feature: 'Guest Comfort',
    hibachi: 'Relaxed home atmosphere',
    restaurant: 'Rushed dining experience',
    hibachiWins: true,
  },
];

// What makes us different from other hibachi caterers
const competitorComparisonItems = [
  {
    feature: 'Chef Quality',
    us: 'Skilled chefs trained in hibachi techniques & food safety',
    others: 'Often untrained cooks with no vetting',
  },
  {
    feature: 'Pricing Transparency',
    us: 'Clear upfront pricing — no hidden fees',
    others: 'Hidden fees, surprise charges after booking',
  },
  {
    feature: 'Dietary Accommodations',
    us: '100% nut-free, sesame-free, halal & kosher options',
    others: 'Limited or no allergen accommodations',
  },
  {
    feature: 'Equipment',
    us: 'We bring everything — professional hibachi grill included',
    others: 'May require you to rent or provide equipment',
  },
  {
    feature: 'Booking Process',
    us: 'Easy online booking with instant confirmation',
    others: 'Slow response, unclear availability',
  },
  {
    feature: 'Service Area',
    us: 'Bay Area, Sacramento & beyond — first 30 miles FREE',
    others: 'Limited areas, high travel fees from mile 1',
  },
  {
    feature: 'Entertainment',
    us: 'Full hibachi show with tricks, fire & fun',
    others: 'Basic cooking, minimal entertainment',
  },
  {
    feature: 'Reliability',
    us: 'Consistent 5-star service, always on time',
    others: 'Inconsistent quality, cancellations happen',
  },
];

const dietaryBadges = [
  { label: '100% Nut-Free', emoji: '🥜' },
  { label: 'Sesame-Free', emoji: '🌾' },
  { label: 'Dairy-Free Butter', emoji: '🧈' },
  { label: 'Gluten-Free Option', emoji: '🌾' },
  { label: 'Halal Certified', emoji: '☪️' },
  { label: 'Kosher-Friendly', emoji: '✡️' },
];

export default function ValuePropositionSection() {
  const { trackPageEngagement } = useAnalytics();
  const {
    adultPrice,
    childPrice,
    childFreeUnderAge,
    partyMinimum,
    depositAmount,
    freeMiles,
    perMileRate,
    isLoading: pricingLoading,
  } = usePricing();

  // Safe display values for template usage
  const displayAdultPrice = pricingLoading || adultPrice === undefined ? '...' : adultPrice;
  const displayChildPrice = pricingLoading || childPrice === undefined ? '...' : childPrice;
  const displayChildFreeUnderAge =
    pricingLoading || childFreeUnderAge === undefined ? 5 : childFreeUnderAge;
  const displayPartyMinimum = pricingLoading || partyMinimum === undefined ? 0 : partyMinimum;
  const displayDepositAmount =
    pricingLoading || depositAmount === undefined ? '...' : depositAmount;
  const displayFreeMiles = pricingLoading || freeMiles === undefined ? 30 : freeMiles;
  const displayPerMileRate = pricingLoading || perMileRate === undefined ? 2 : perMileRate;

  return (
    <section className="value-proposition-section bg-gradient-to-br from-gray-50 to-gray-100 py-20">
      <div className="container mx-auto max-w-6xl px-4">
        {/* Section Header */}
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-4xl font-bold text-gray-800 md:text-5xl">
            Why Choose My Hibachi Chef?
          </h2>
          <p className="mx-auto max-w-3xl text-xl text-gray-600">
            Bring the authentic hibachi experience to your home. Professional chefs, premium
            ingredients, and unforgettable entertainment — all in your own backyard.
          </p>
        </div>

        {/* What's Included Grid */}
        <div className="mb-16">
          <h3 className="mb-8 text-center text-2xl font-bold text-gray-800">
            Everything Included in Your Experience
          </h3>
          <div className="grid gap-4 md:grid-cols-2">
            {includedItems.map((item, index) => (
              <div
                key={index}
                className="group relative flex items-start gap-4 rounded-xl bg-white p-5 shadow-md transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg"
              >
                {/* Icon - Side aligned */}
                <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-red-500 to-orange-500 text-white shadow-sm transition-all duration-300 group-hover:scale-105 group-hover:shadow-md">
                  {item.icon}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="text-base font-bold text-gray-800">{item.title}</h4>
                    {item.highlight && (
                      <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-700">
                        {item.highlight}
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-sm leading-relaxed text-gray-600">{item.description}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Upgrades & Add-ons Grid */}
          <div className="mt-10">
            <h4 className="mb-6 text-center text-xl font-bold text-gray-700">
              ✨ Customize Your Experience
            </h4>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {upgradeItems.map((upgrade, index) => (
                <div
                  key={index}
                  className="group rounded-xl border-2 border-dashed border-amber-300 bg-gradient-to-br from-amber-50 to-orange-50 p-5 transition-all duration-300 hover:border-amber-400 hover:shadow-md"
                >
                  <div className="mb-3 flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-100 text-amber-600 transition-transform group-hover:scale-110">
                      {upgrade.icon}
                    </div>
                    <div>
                      <h5 className="font-bold text-gray-800">{upgrade.title}</h5>
                      <span className="text-xs text-gray-500">({upgrade.note})</span>
                    </div>
                  </div>
                  <ul className="space-y-1.5">
                    {upgrade.items.map((item, i) => (
                      <li key={i} className="flex items-center justify-between text-sm">
                        <span className="flex items-center gap-2 text-gray-600">
                          <Check className="h-3.5 w-3.5 flex-shrink-0 text-green-500" />
                          {item.name}
                        </span>
                        <span className="font-semibold text-amber-600">{item.price}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Comparison: Us vs Restaurant */}
        <div className="mb-16">
          <h3 className="mb-8 text-center text-2xl font-bold text-gray-800">
            Private Hibachi vs. Restaurant Dining
          </h3>
          <div className="overflow-hidden rounded-xl bg-white shadow-lg">
            <div className="hidden bg-gray-800 text-white md:grid md:grid-cols-3">
              <div className="p-4 font-semibold">Feature</div>
              <div className="bg-gradient-to-r from-red-600 to-orange-600 p-4 text-center font-semibold">
                🔥 My Hibachi Chef
              </div>
              <div className="p-4 text-center font-semibold">Restaurant</div>
            </div>
            {comparisonItems.map((item, index) => (
              <div
                key={index}
                className={`grid md:grid-cols-3 ${index % 2 === 0 ? 'bg-gray-50' : 'bg-white'}`}
              >
                <div className="border-b p-4 font-medium text-gray-700 md:border-b-0">
                  <span className="font-semibold text-gray-500 md:hidden">Feature: </span>
                  {item.feature}
                </div>
                <div className="border-b p-4 text-center md:border-b-0">
                  <span className="mb-1 block font-semibold text-gray-500 md:hidden">
                    My Hibachi:
                  </span>
                  <span className="inline-flex items-center gap-2 font-medium text-green-700">
                    <Check className="h-5 w-5 text-green-600" />
                    {item.hibachi}
                  </span>
                </div>
                <div className="border-b p-4 text-center text-gray-500 md:border-b-0">
                  <span className="mb-1 block font-semibold text-gray-500 md:hidden">
                    Restaurant:
                  </span>
                  {item.restaurant}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Competitor Comparison - Us vs Other Caterers */}
        <div className="mb-16">
          <h3 className="mb-8 text-center text-2xl font-bold text-gray-800">
            Why Choose Us Over Other Hibachi Caterers?
          </h3>
          <div className="overflow-hidden rounded-xl bg-white shadow-lg">
            <div className="hidden bg-gray-800 text-white md:grid md:grid-cols-3">
              <div className="p-4 font-semibold">What Matters</div>
              <div className="bg-gradient-to-r from-red-600 to-orange-600 p-4 text-center font-semibold">
                ⭐ My Hibachi Chef
              </div>
              <div className="p-4 text-center font-semibold">Other Caterers</div>
            </div>
            {competitorComparisonItems.map((item, index) => (
              <div
                key={index}
                className={`grid md:grid-cols-3 ${index % 2 === 0 ? 'bg-gray-50' : 'bg-white'}`}
              >
                <div className="border-b p-4 font-medium text-gray-700 md:border-b-0">
                  <span className="font-semibold text-gray-500 md:hidden">Feature: </span>
                  {item.feature}
                </div>
                <div className="border-b p-4 text-center md:border-b-0">
                  <span className="mb-1 block font-semibold text-gray-500 md:hidden">
                    My Hibachi:
                  </span>
                  <span className="inline-flex items-center gap-2 font-medium text-green-700">
                    <Check className="h-5 w-5 flex-shrink-0 text-green-600" />
                    <span className="text-left">{item.us}</span>
                  </span>
                </div>
                <div className="border-b p-4 text-center text-gray-500 md:border-b-0">
                  <span className="mb-1 block font-semibold text-gray-500 md:hidden">Others:</span>
                  <span className="inline-flex items-center gap-2">
                    <X className="h-5 w-5 flex-shrink-0 text-red-400" />
                    <span className="text-left">{item.others}</span>
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Dietary Advantages */}
        <div className="mb-16">
          <h3 className="mb-6 text-center text-2xl font-bold text-gray-800">
            Allergen-Friendly Kitchen
          </h3>
          <p className="mx-auto mb-8 max-w-2xl text-center text-gray-600">
            Unlike most hibachi restaurants, we take dietary restrictions seriously. Our kitchen is
            designed to accommodate various dietary needs.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            {dietaryBadges.map((badge, index) => (
              <span
                key={index}
                className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-md transition-all hover:shadow-lg"
              >
                <span>{badge.emoji}</span>
                {badge.label}
              </span>
            ))}
          </div>
        </div>

        {/* Chef Quality Callout */}
        <div className="mb-16 rounded-2xl bg-gradient-to-r from-gray-800 to-gray-900 p-8 text-white md:p-12">
          <div className="grid items-center gap-8 md:grid-cols-2">
            <div>
              <h3 className="mb-4 text-3xl font-bold">Professionally Trained Hibachi Chefs</h3>
              <p className="mb-6 text-lg text-gray-300">
                Our chefs are experienced professionals — not random cooks. Each chef is trained in
                authentic hibachi techniques, food safety, and entertainment. You get
                restaurant-quality cooking with a personal touch.
              </p>
              <ul className="space-y-3">
                <li className="flex items-center gap-3">
                  <Check className="h-5 w-5 text-green-400" />
                  <span>Trained in authentic teppanyaki techniques</span>
                </li>
                <li className="flex items-center gap-3">
                  <Check className="h-5 w-5 text-green-400" />
                  <span>Food safety certified</span>
                </li>
                <li className="flex items-center gap-3">
                  <Check className="h-5 w-5 text-green-400" />
                  <span>Entertaining & professional performance</span>
                </li>
              </ul>
            </div>
            <div className="flex justify-center">
              <div className="relative">
                <div className="flex h-48 w-48 items-center justify-center rounded-full bg-gradient-to-r from-red-500 to-orange-500">
                  <ChefHat className="h-24 w-24 text-white" />
                </div>
                <div className="absolute -right-2 -bottom-2 rounded-full bg-green-500 px-4 py-2 text-sm font-bold text-white shadow-lg">
                  Expert Chefs
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Urgency Section */}
        <div className="mb-12 rounded-2xl bg-gradient-to-r from-red-600 to-orange-600 p-8 text-white md:p-12">
          <div className="text-center">
            <h3 className="mb-4 text-3xl font-bold md:text-4xl">🔥 Limited Chef Availability</h3>
            <p className="mx-auto mb-8 max-w-2xl text-lg text-red-100">
              We have a limited number of experienced chefs, and weekends book out fast! Secure your
              date early to avoid disappointment.
            </p>

            {/* Booking Tips */}
            <div className="mb-8 grid gap-4 md:grid-cols-3">
              <div className="rounded-xl bg-white/10 p-4 backdrop-blur-sm">
                <Calendar className="mx-auto mb-2 h-8 w-8" />
                <h4 className="font-bold">Weekends</h4>
                <p className="text-sm text-red-100">Book 1-2 weeks ahead — fills up quickly!</p>
              </div>
              <div className="rounded-xl bg-white/10 p-4 backdrop-blur-sm">
                <Clock className="mx-auto mb-2 h-8 w-8" />
                <h4 className="font-bold">Weekdays</h4>
                <p className="text-sm text-red-100">At least 1 week in advance recommended</p>
              </div>
              <div className="rounded-xl bg-white/10 p-4 backdrop-blur-sm">
                <Zap className="mx-auto mb-2 h-8 w-8" />
                <h4 className="font-bold">Minimum Notice</h4>
                <p className="text-sm text-red-100">48 hours required for all bookings</p>
              </div>
            </div>

            {/* Service Area */}
            <div className="mb-8 flex items-center justify-center gap-2 text-red-100">
              <MapPin className="h-5 w-5" />
              <span>Serving Bay Area, Sacramento & Northern California</span>
            </div>

            {/* CTA Buttons - Enhanced Design */}
            <div className="flex flex-col justify-center gap-4 sm:flex-row">
              <Link
                href="/book-us/"
                className="group relative inline-flex transform items-center justify-center gap-3 overflow-hidden rounded-xl bg-white px-8 py-4 text-lg font-bold text-red-600 shadow-lg transition-all duration-300 hover:scale-105 hover:shadow-2xl"
                onClick={() => trackPageEngagement('click', 'value_prop_book_now_cta')}
              >
                <span className="absolute inset-0 bg-gradient-to-r from-red-50 to-orange-50 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
                <Calendar className="relative h-5 w-5 transition-transform group-hover:scale-110" />
                <span className="relative">Book Your Date Now</span>
                <ArrowRight className="relative h-5 w-5 transition-transform group-hover:translate-x-1" />
              </Link>
              <Link
                href="/quote"
                className="group relative inline-flex items-center justify-center gap-3 overflow-hidden rounded-xl border-2 border-white bg-white/5 px-8 py-4 text-lg font-bold text-white backdrop-blur-sm transition-all duration-300 hover:bg-white hover:text-red-600"
                onClick={() => trackPageEngagement('click', 'value_prop_get_quote_cta')}
              >
                <Users className="h-5 w-5 transition-transform group-hover:scale-110" />
                <span>Get Your Quote</span>
                <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
              </Link>
            </div>
          </div>
        </div>

        {/* Quick Contact */}
        <div className="text-center">
          <p className="mb-4 text-gray-600">Have questions? We&apos;re here to help!</p>
          <a
            href="tel:9167408768"
            className="inline-flex items-center gap-2 text-2xl font-bold text-red-600 transition-colors hover:text-red-700"
            onClick={() => trackPageEngagement('click', 'value_prop_phone_cta')}
          >
            <Phone className="h-6 w-6" />
            (916) 740-8768
          </a>
          <p className="mt-2 text-sm text-gray-500">Text or call for instant assistance</p>
        </div>

        {/* Pricing Transparency */}
        <div className="mt-12 rounded-xl bg-white p-8 shadow-lg">
          <h3 className="mb-6 text-center text-2xl font-bold text-gray-800">Transparent Pricing</h3>
          <div className="grid gap-6 text-center md:grid-cols-3">
            <div className="p-4">
              <div className="mb-2 text-4xl font-bold text-red-600">${displayAdultPrice}</div>
              <div className="text-gray-600">Per Adult (13+)</div>
            </div>
            <div className="p-4">
              <div className="mb-2 text-4xl font-bold text-red-600">${displayChildPrice}</div>
              <div className="text-gray-600">Per Child ({displayChildFreeUnderAge + 1}-12)</div>
            </div>
            <div className="p-4">
              <div className="mb-2 text-4xl font-bold text-green-600">FREE</div>
              <div className="text-gray-600">Ages {displayChildFreeUnderAge} & Under</div>
            </div>
          </div>
          <div className="mt-6 text-center">
            <p className="text-gray-600">
              <span className="font-semibold">${displayPartyMinimum} minimum</span> (approximately{' '}
              {displayPartyMinimum && displayAdultPrice !== '...'
                ? Math.ceil(displayPartyMinimum / Number(displayAdultPrice))
                : '...'}{' '}
              adults) •
              <span className="font-semibold"> ${displayDepositAmount} refundable deposit</span>{' '}
              secures your date
            </p>
            <p className="mt-2 text-sm text-gray-500">
              First {displayFreeMiles} miles free travel • ${displayPerMileRate}/mile after
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
