'use client';

import '@/styles/base.css';

import { useProtectedPhone, ProtectedEmail } from '@/components/ui/ProtectedPhone';
import {
  ShieldCheck,
  AlertTriangle,
  ClipboardList,
  PlusCircle,
  XCircle,
  CheckCircle,
  Info,
  ShieldAlert,
  MessageSquare,
  AlertOctagon,
  Heart,
  Mail,
  Phone,
  CalendarCheck,
} from 'lucide-react';

// Metadata moved to layout.tsx for server component support
// export const metadata: Metadata = {...}

export default function AllergensPage() {
  // Anti-scraper protected contact info
  const { formatted: protectedPhone, tel: protectedTel } = useProtectedPhone();

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-center">
        <div className="w-full lg:w-5/6">
          {/* Header */}
          <div className="mb-5 text-center">
            <h1 className="display-4 mb-3">
              <ShieldCheck className="mr-3 inline-block h-10 w-10 text-blue-500" />
              Allergen Information & Safety Guide
            </h1>
            <p className="lead text-muted">
              Your safety is our priority. Below is comprehensive allergen information for our
              hibachi catering services.
            </p>
          </div>

          {/* Critical Warning */}
          <div className="alert alert-danger mb-5" role="alert">
            <h4 className="alert-heading flex items-center">
              <AlertTriangle className="mr-2 h-6 w-6" />
              Critical Information - Please Read
            </h4>
            <p className="mb-2">
              <strong>Cross-Contamination Risk:</strong> We use shared cooking surfaces, utensils,
              and oils at all events. While we take every reasonable precaution to accommodate
              dietary restrictions, we{' '}
              <strong className="text-decoration-underline">
                CANNOT GUARANTEE a 100% allergen-free environment
              </strong>{' '}
              for customers with severe allergies.
            </p>
            <hr />
            <p className="mb-0">
              <strong>If you have severe allergies:</strong> Please communicate this information to
              our staff at booking and again via SMS/phone before your event. We will work with you
              to minimize risk, but you must make an informed decision about your safety.
            </p>
          </div>

          {/* FDA Major 9 Allergens */}
          <section className="mb-5">
            <h2 className="mb-4 flex items-center">
              <ClipboardList className="mr-2 h-6 w-6 text-blue-500" />
              FDA Major 9 Allergens in Our Kitchen
            </h2>
            <p className="mb-4">
              These allergens account for 90% of all food allergies and are present in our standard
              hibachi menu:
            </p>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {/* Shellfish */}
              <div>
                <div className="card border-danger h-100">
                  <div className="card-body">
                    <h5 className="card-title text-danger flex items-center">
                      <span className="mr-2 flex h-6 w-6 items-center justify-center rounded-full bg-red-500 text-sm font-bold text-white">1</span>
                      Shellfish 🦞
                    </h5>
                    <p>
                      <strong>Contains:</strong> Shrimp, Lobster, Scallops
                    </p>
                    <p>
                      <strong>Found in:</strong> Premium protein options
                    </p>
                    <p className="mb-0">
                      <strong>Safe alternatives:</strong> Chicken, Steak, Salmon (fish), Tofu
                    </p>
                  </div>
                </div>
              </div>

              {/* Fish */}
              <div className="">
                <div className="card border-danger h-100">
                  <div className="card-body">
                    <h5 className="card-title text-danger flex items-center">
                      <span className="mr-2 flex h-6 w-6 items-center justify-center rounded-full bg-red-500 text-sm font-bold text-white">2</span>
                      Fish 🐟
                    </h5>
                    <p>
                      <strong>Contains:</strong> Salmon (finned fish)
                    </p>
                    <p>
                      <strong>Found in:</strong> Premium protein upgrade
                    </p>
                    <p className="mb-0">
                      <strong>Note:</strong> Fish allergy is separate from shellfish allergy
                    </p>
                  </div>
                </div>
              </div>

              {/* Gluten */}
              <div className="">
                <div className="card border-warning h-100">
                  <div className="card-body">
                    <h5 className="card-title text-warning flex items-center">
                      <span className="mr-2 flex h-6 w-6 items-center justify-center rounded-full bg-yellow-500 text-sm font-bold text-white">3</span>
                      Gluten (Wheat) 🌾
                    </h5>
                    <p>
                      <strong>Contains:</strong> Wheat protein
                    </p>
                    <p>
                      <strong>Found in:</strong> Chicken Gyoza (wrapper), Egg Noodles, Teriyaki
                      Sauce (soy sauce contains wheat)
                    </p>
                    <p className="mb-0">
                      <strong>Gluten-free options:</strong> Gluten-free soy sauce available upon
                      request, skip gyoza/noodles
                    </p>
                  </div>
                </div>
              </div>

              {/* Soy */}
              <div className="">
                <div className="card border-warning h-100">
                  <div className="card-body">
                    <h5 className="card-title text-warning flex items-center">
                      <span className="mr-2 flex h-6 w-6 items-center justify-center rounded-full bg-yellow-500 text-sm font-bold text-white">4</span>
                      Soy 🫘
                    </h5>
                    <p>
                      <strong>Contains:</strong> Soybeans
                    </p>
                    <p>
                      <strong>Found in:</strong> Soy sauce (teriyaki, yum yum), Tofu, Edamame
                    </p>
                    <p className="mb-0">
                      <strong>Note:</strong> Soy sauce is in most hibachi sauces
                    </p>
                  </div>
                </div>
              </div>

              {/* Eggs */}
              <div className="">
                <div className="card border-info h-100">
                  <div className="card-body">
                    <h5 className="card-title text-info flex items-center">
                      <span className="mr-2 flex h-6 w-6 items-center justify-center rounded-full bg-blue-500 text-sm font-bold text-white">5</span>
                      Eggs 🥚
                    </h5>
                    <p>
                      <strong>Contains:</strong> Chicken eggs
                    </p>
                    <p>
                      <strong>Found in:</strong> Hibachi Fried Rice
                    </p>
                    <p className="mb-0">
                      <strong>Safe alternative:</strong> Plain steamed rice (upon request)
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Additional Allergens */}
          <section className="mb-5">
            <h2 className="mb-4 flex items-center">
              <PlusCircle className="mr-2 h-6 w-6 text-blue-500" />
              Additional Allergens We Track
            </h2>
            <p className="mb-4">
              Beyond the FDA Major 9, we also track these allergens used in our menu:
            </p>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {/* Celery */}
              <div className="">
                <div className="card border-secondary h-100">
                  <div className="card-body">
                    <h5 className="card-title">Celery 🥬</h5>
                    <p>
                      <strong>Found in:</strong> Salad dressing
                    </p>
                    <p className="mb-0">
                      <strong>EU allergen</strong> - Can cause severe reactions in sensitive
                      individuals
                    </p>
                  </div>
                </div>
              </div>

              {/* Corn */}
              <div className="">
                <div className="card border-secondary h-100">
                  <div className="card-body">
                    <h5 className="card-title">Corn 🌽</h5>
                    <p>
                      <strong>Found in:</strong> Corn starch (in teriyaki sauce)
                    </p>
                    <p className="mb-0">Typically mild allergen, but we track for safety</p>
                  </div>
                </div>
              </div>

              {/* Sulfites */}
              <div className="">
                <div className="card border-secondary h-100">
                  <div className="card-body">
                    <h5 className="card-title">Sulfites 🍶</h5>
                    <p>
                      <strong>Found in:</strong> Sake (Japanese rice wine)
                    </p>
                    <p className="mb-0">
                      <strong>Note:</strong> We do NOT use vinegar, so sulfites are minimal
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* What We DON'T Use */}
          <section className="mb-5">
            <h2 className="mb-4 flex items-center">
              <XCircle className="mr-2 h-6 w-6 text-green-500" />
              Allergens We DO NOT Use
            </h2>
            <p className="mb-3">
              The following common allergens are <strong>NOT</strong> present in our standard menu:
            </p>
            <div className="row">
              <div className="">
                <ul className="list-group">
                  <li className="list-group-item flex items-center">
                    <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
                    <strong>Peanuts</strong> - NOT used
                  </li>
                  <li className="list-group-item flex items-center">
                    <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
                    <strong>Tree Nuts</strong> - NOT used
                  </li>
                  <li className="list-group-item flex items-center">
                    <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
                    <strong>Dairy/Milk</strong> - NOT used (butter substitute only)
                  </li>
                  <li className="list-group-item flex items-center">
                    <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
                    <strong>Sesame Oil</strong> - NOT used
                  </li>
                </ul>
              </div>
              <div className="">
                <ul className="list-group">
                  <li className="list-group-item flex items-center">
                    <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
                    <strong>MSG</strong> - NOT used
                  </li>
                  <li className="list-group-item flex items-center">
                    <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
                    <strong>Mustard</strong> - NOT used
                  </li>
                  <li className="list-group-item flex items-center">
                    <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
                    <strong>Bell Peppers</strong> - NOT used
                  </li>
                  <li className="list-group-item flex items-center">
                    <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
                    <strong>Vinegar</strong> - NOT used
                  </li>
                </ul>
              </div>
            </div>
            <div className="alert alert-info mt-3 flex items-center" role="alert">
              <Info className="mr-2 h-5 w-5" />
              <span><strong>Our cooking oil:</strong> We use <strong>canola oil</strong>, which is
                allergen-free and does NOT contain soy.</span>
            </div>
          </section>

          {/* Cross-Contamination Protocols */}
          <section className="mb-5">
            <h2 className="mb-4 flex items-center">
              <ShieldAlert className="mr-2 h-6 w-6 text-yellow-500" />
              Cross-Contamination Protocols
            </h2>
            <div className="card border-warning mb-3">
              <div className="card-body">
                <h5 className="card-title text-warning">Our Safety Measures:</h5>
                <ul className="mb-0">
                  <li>
                    <strong>Separate preparation areas</strong> for allergen-free requests when
                    possible
                  </li>
                  <li>
                    <strong>Clean utensils</strong> used for customers with severe allergies
                  </li>
                  <li>
                    <strong>Chef notification system</strong> - Your allergies are flagged in our
                    booking system
                  </li>
                  <li>
                    <strong>Ingredient awareness training</strong> - All chefs know our allergen
                    list
                  </li>
                </ul>
              </div>
            </div>
            <div className="card border-danger">
              <div className="card-body">
                <h5 className="card-title text-danger">⚠️ Limitations:</h5>
                <ul className="mb-0">
                  <li>
                    We use <strong>shared cooking surfaces</strong> (hibachi grill) for all proteins
                  </li>
                  <li>
                    We use <strong>shared oil</strong> (canola) for all cooking
                  </li>
                  <li>
                    We use <strong>shared utensils</strong> (spatulas, knives) during service
                  </li>
                  <li>
                    Airborne particles from cooking shellfish, fish, and soy sauce may be present
                  </li>
                </ul>
              </div>
            </div>
          </section>

          {/* How to Communicate Allergies */}
          <section className="mb-5">
            <h2 className="mb-4 flex items-center">
              <MessageSquare className="mr-2 h-6 w-6 text-blue-500" />
              How to Communicate Your Allergies
            </h2>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="">
                <div className="card bg-light h-100">
                  <div className="card-body text-center">
                    <span className="flex h-12 w-12 mx-auto items-center justify-center rounded-full bg-blue-500 text-xl font-bold text-white">1</span>
                    <h5 className="mt-3">At Booking</h5>
                    <p className="mb-0">
                      Include all allergies in the &ldquo;Special Requests&rdquo; field when booking
                      online or mention them via text/phone
                    </p>
                  </div>
                </div>
              </div>
              <div className="">
                <div className="card bg-light h-100">
                  <div className="card-body text-center">
                    <span className="flex h-12 w-12 mx-auto items-center justify-center rounded-full bg-blue-500 text-xl font-bold text-white">2</span>
                    <h5 className="mt-3">SMS Confirmation</h5>
                    <p className="mb-0">
                      When you receive booking confirmation via SMS, we will ask you to confirm
                      allergies again
                    </p>
                  </div>
                </div>
              </div>
              <div className="">
                <div className="card bg-light h-100">
                  <div className="card-body text-center">
                    <span className="flex h-12 w-12 mx-auto items-center justify-center rounded-full bg-blue-500 text-xl font-bold text-white">3</span>
                    <h5 className="mt-3">Before Event</h5>
                    <p className="mb-0">
                      Speak directly with your chef upon arrival to review allergies and safe menu
                      options
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Emergency Contact */}
          <section className="mb-5">
            <div className="card bg-danger text-white">
              <div className="card-body">
                <h3 className="card-title flex items-center">
                  <AlertOctagon className="mr-2 h-7 w-7" />
                  Emergency / Severe Allergies
                </h3>
                <p className="mb-3">
                  If you or your guests have <strong>severe, life-threatening allergies</strong>{' '}
                  (anaphylaxis risk):
                </p>
                <ul className="mb-3">
                  <li>Contact us BEFORE booking to discuss safety protocols</li>
                  <li>Ensure you have an EpiPen or emergency medication on-site</li>
                  <li>Consider whether shared cooking surfaces present acceptable risk</li>
                  <li>We reserve the right to decline service if we cannot safely accommodate</li>
                </ul>
                <p className="mb-0">
                  <strong>Contact:</strong>{' '}
                  <ProtectedEmail className="text-decoration-underline text-white" /> or text{' '}
                  <a
                    href={protectedTel ? `tel:${protectedTel}` : '#'}
                    className="text-decoration-underline text-white"
                  >
                    {protectedPhone || 'Loading...'}
                  </a>
                </p>
              </div>
            </div>
          </section>

          {/* Dietary Accommodations */}
          <section className="mb-5">
            <h2 className="mb-4 flex items-center">
              <Heart className="mr-2 h-6 w-6 text-red-500" />
              Dietary Accommodations We Offer
            </h2>
            <p className="mb-3">
              We can accommodate many dietary needs with advance notice (48+ hours):
            </p>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="">
                <div className="card">
                  <div className="card-body">
                    <h5 className="card-title flex items-center">
                      <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
                      Vegetarian / Vegan
                    </h5>
                    <p className="mb-0">
                      Tofu, extra vegetables, egg-free fried rice (vegan), no animal products
                    </p>
                  </div>
                </div>
              </div>
              <div className="">
                <div className="card">
                  <div className="card-body">
                    <h5 className="card-title flex items-center">
                      <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
                      Gluten-Free
                    </h5>
                    <p className="mb-0">
                      Gluten-free soy sauce, skip gyoza/noodles, all proteins are naturally
                      gluten-free
                    </p>
                  </div>
                </div>
              </div>
              <div className="">
                <div className="card">
                  <div className="card-body">
                    <h5 className="card-title flex items-center">
                      <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
                      Dairy-Free
                    </h5>
                    <p className="mb-0">
                      Our standard menu is dairy-free (we use butter substitute, not real butter)
                    </p>
                  </div>
                </div>
              </div>
              <div className="">
                <div className="card">
                  <div className="card-body">
                    <h5 className="card-title flex items-center">
                      <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
                      Halal / Kosher
                    </h5>
                    <p className="mb-0">
                      We can source halal/kosher proteins with advance notice - contact us to
                      discuss
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Footer CTA */}
          <div className="border-t border-gray-200 mt-8 pt-8 text-center">
            <h3 className="text-2xl font-bold text-gray-800 mb-3">Questions About Allergens?</h3>
            <p className="text-lg text-gray-600 mb-6">
              We&apos;re here to help ensure your event is safe and enjoyable for all guests.
            </p>
            <div className="flex justify-center flex-wrap gap-4">
              <a
                href="/contact"
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 text-white font-semibold rounded-xl shadow-md hover:from-red-700 hover:to-red-800 hover:shadow-lg transition-all duration-300"
              >
                <Mail className="h-5 w-5" />
                Contact Us
              </a>
              <a
                href={protectedTel ? `tel:${protectedTel}` : '#'}
                className="inline-flex items-center gap-2 px-6 py-3 border-2 border-red-600 text-red-600 font-semibold rounded-xl hover:bg-red-50 hover:border-red-700 hover:text-red-700 transition-all duration-300"
              >
                <Phone className="h-5 w-5" />
                Call {protectedPhone || 'Loading...'}
              </a>
              <a
                href="/BookUs"
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white font-semibold rounded-xl shadow-md hover:from-green-700 hover:to-green-800 hover:shadow-lg transition-all duration-300"
              >
                <CalendarCheck className="h-5 w-5" />
                Book Your Event
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
