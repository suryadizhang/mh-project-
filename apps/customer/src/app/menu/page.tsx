'use client';

// Menu page-specific CSS
import '@/styles/menu.css';
import '@/styles/menu/menu-features.css';
import '@/styles/menu/menu-pricing.css';
import '@/styles/menu/menu-base.css';
import '@/styles/menu/base.css';
import '@/styles/pages/menu.page.css';

import { Calculator, Calendar, ChevronDown, ChevronUp, MessageCircle } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';

import { usePricing } from '@/hooks/usePricing';
import { CenteredFlexGrid } from '@/components/ui/CenteredFlexGrid';

export default function MenuPage() {
  const [isProteinsOpen, setIsProteinsOpen] = useState(false);
  const [isAdditionsOpen, setIsAdditionsOpen] = useState(false);

  // Get dynamic pricing values - API is source of truth
  const {
    adultPrice,
    childPrice,
    partyMinimum,
    childFreeUnderAge,
    freeMiles,
    perMileRate,
    // Premium protein upgrades (SSoT)
    salmonUpgradePrice,
    scallopsUpgradePrice,
    filetMignonUpgradePrice,
    lobsterTailUpgradePrice,
    extraProteinPrice,
    // Addon items (SSoT)
    yakisobaNoodlesPrice,
    extraFriedRicePrice,
    extraVegetablesPrice,
    edamamePrice,
    gyozaPrice,
    isLoading: pricingLoading,
  } = usePricing();

  // Safe pricing display values (show placeholder during loading)
  const displayAdultPrice = pricingLoading || adultPrice === undefined ? '...' : adultPrice;
  const displayChildPrice = pricingLoading || childPrice === undefined ? '...' : childPrice;
  const displayPartyMinimum = pricingLoading || partyMinimum === undefined ? 0 : partyMinimum;
  const displayChildFreeUnderAge =
    pricingLoading || childFreeUnderAge === undefined ? 5 : childFreeUnderAge;
  const displayFreeMiles = pricingLoading || freeMiles === undefined ? '...' : freeMiles;
  const displayPerMileRate = pricingLoading || perMileRate === undefined ? '...' : perMileRate;

  // Upgrade prices (SSoT) - show '...' during loading, default to $5/$10/$15 if undefined
  const displaySalmonPrice = pricingLoading ? '...' : (salmonUpgradePrice ?? 5);
  const displayScallopsPrice = pricingLoading ? '...' : (scallopsUpgradePrice ?? 5);
  const displayFiletPrice = pricingLoading ? '...' : (filetMignonUpgradePrice ?? 5);
  const displayLobsterPrice = pricingLoading ? '...' : (lobsterTailUpgradePrice ?? 15);
  const displayExtraProteinPrice = pricingLoading ? '...' : (extraProteinPrice ?? 10);

  // Addon prices (SSoT) - show '...' during loading, default to $5/$10 if undefined
  const displayYakisobaPrice = pricingLoading ? '...' : (yakisobaNoodlesPrice ?? 5);
  const displayExtraRicePrice = pricingLoading ? '...' : (extraFriedRicePrice ?? 5);
  const displayExtraVeggiesPrice = pricingLoading ? '...' : (extraVegetablesPrice ?? 5);
  const displayEdamamePrice = pricingLoading ? '...' : (edamamePrice ?? 5);
  const displayGyozaPrice = pricingLoading ? '...' : (gyozaPrice ?? 10);

  return (
    <main>
      {/* Menu Container */}
      <div className="menu-container">
        <div className="container-fluid px-lg-5">
          {/* Enhanced Hero Section with Better Flow */}
          <div className="hero-section page-hero-background mb-5 text-center">
            <div className="hero-content">
              <div className="hero-icon-wrapper mb-4">
                <div className="glow-icon-container">
                  <span className="hero-main-icon glow-icon emoji-visible">🍱</span>
                </div>
              </div>

              <h1 className="display-1 fw-bold mb-4">
                <span className="gradient-text">Premium Hibachi Menu</span>
              </h1>

              <p className="hero-subtitle mb-4">
                <span className="emoji-visible">✨</span>
                Experience authentic Japanese hibachi dining in the comfort of your home
                <span className="emoji-visible">✨</span>
              </p>

              {/* Enhanced Value Proposition */}
              <div className="value-proposition mb-5">
                <div className="value-item">
                  <span className="value-icon emoji-visible">🚚</span>
                  <span className="value-text">We Come to You</span>
                </div>
                <div className="value-divider">•</div>
                <div className="value-item">
                  <span className="value-icon emoji-visible">👨‍🍳</span>
                  <span className="value-text">Professional Chef</span>
                </div>
                <div className="value-divider">•</div>
                <div className="value-item">
                  <span className="value-icon emoji-visible">🎭</span>
                  <span className="value-text">Live Entertainment</span>
                </div>
              </div>

              {/* Enhanced feature badges with better animations */}
              <div className="hero-features-grid mb-5">
                <div className="feature-badge modern-feature-badge">
                  <div className="feature-icon-bg">
                    <span className="feature-icon emoji-visible">⭐</span>
                  </div>
                  <div className="feature-content">
                    <span className="feature-title">Premium Quality</span>
                    <span className="feature-subtitle">Fresh ingredients</span>
                  </div>
                </div>

                <div className="feature-badge modern-feature-badge">
                  <div className="feature-icon-bg">
                    <span className="feature-icon emoji-visible">🔧</span>
                  </div>
                  <div className="feature-content">
                    <span className="feature-title">Custom Experience</span>
                    <span className="feature-subtitle">Tailored to you</span>
                  </div>
                </div>
                <div className="feature-badge modern-feature-badge">
                  <div className="feature-icon-bg">
                    <span className="feature-icon emoji-visible">💎</span>
                  </div>
                  <div className="feature-content">
                    <span className="feature-title">Luxury Service</span>
                    <span className="feature-subtitle">Premium quality</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Modernized Pricing Section */}
          <div className="card menu-card mb-5 overflow-hidden border-0 p-0">
            <div className="pricing-section compact-pricing mb-0 p-5">
              <div className="mb-5 text-center">
                <div className="section-header animated-section">
                  <div className="section-icon-wrapper mb-3">
                    <span className="section-icon emoji-visible">💰</span>
                  </div>
                  <h2 className="section-title mb-4">
                    <span>Transparent Pricing</span>
                  </h2>
                  <p className="section-subtitle">
                    Premium experience, honest pricing — no hidden fees
                  </p>
                </div>
              </div>

              {/* Enhanced pricing cards */}
              <div className="mb-8 flex justify-center">
                <div className="w-full">
                  <div className="pricing-cards-container">
                    <div className="pricing-card modern-card adult-price" data-price="adult">
                      <div className="card-glow"></div>
                      <div className="card-header-accent"></div>
                      <div className="pricing-icon-container">
                        <span className="pricing-icon emoji-visible">👨‍👩‍👧‍👦</span>
                      </div>
                      <div className="pricing-amount">${displayAdultPrice}</div>
                      <div className="pricing-label">per adult</div>
                      <div className="pricing-note">Ages 13+</div>
                      <div className="card-features">
                        <div className="feature">
                          <span className="feature-check">✓</span>
                          <span>Full hibachi experience</span>
                        </div>
                        <div className="feature">
                          <span className="feature-check">✓</span>
                          <span>2 protein choices</span>
                        </div>
                        <div className="feature">
                          <span className="feature-check">✓</span>
                          <span>All sides included</span>
                        </div>
                      </div>
                    </div>

                    <div className="pricing-card modern-card child-price" data-price="child">
                      <div className="card-glow"></div>
                      <div className="card-header-accent"></div>
                      <div className="pricing-icon-container">
                        <span className="pricing-icon emoji-visible">🧒</span>
                      </div>
                      <div className="pricing-amount">${displayChildPrice}</div>
                      <div className="pricing-label">per child</div>
                      <div className="pricing-note">Ages {displayChildFreeUnderAge + 1}-12</div>
                      <div className="card-features">
                        <div className="feature">
                          <span className="feature-check">✓</span>
                          <span>Kid-friendly portions</span>
                        </div>
                        <div className="feature">
                          <span className="feature-check">✓</span>
                          <span>1 protein choice</span>
                        </div>
                        <div className="feature">
                          <span className="feature-check">✓</span>
                          <span>All sides included</span>
                        </div>
                      </div>
                    </div>

                    <div className="pricing-card modern-card toddler-price" data-price="toddler">
                      <div className="card-glow"></div>
                      <div className="card-header-accent"></div>
                      <div className="pricing-icon-container">
                        <span className="pricing-icon emoji-visible">👶</span>
                      </div>
                      <div className="pricing-amount">FREE</div>
                      <div className="pricing-label">for toddlers</div>
                      <div className="pricing-note">Ages {displayChildFreeUnderAge} & under</div>
                      <div className="card-features">
                        <div className="feature">
                          <span className="feature-check">✓</span>
                          <span>With adult purchase</span>
                        </div>
                        <div className="feature">
                          <span className="feature-check">✓</span>
                          <span>Small portions</span>
                        </div>
                        <div className="feature">
                          <span className="feature-check">✓</span>
                          <span>Kid-friendly options</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="pricing-footer">
                <div className="info-cards-grid">
                  <div className="info-card">
                    <div className="info-icon">
                      <span className="emoji-visible">🎯</span>
                    </div>
                    <div className="info-content">
                      <h5>Party Minimum</h5>
                      <p>
                        ${displayPartyMinimum} total order (≈{' '}
                        {displayPartyMinimum && displayAdultPrice !== '...'
                          ? Math.ceil(displayPartyMinimum / Number(displayAdultPrice))
                          : '...'}{' '}
                        adults)
                      </p>
                    </div>
                  </div>

                  <div className="info-card">
                    <div className="info-icon">
                      <span className="emoji-visible">💡</span>
                    </div>
                    <div className="info-content">
                      <h5>Gratuity Guide</h5>
                      <p>20-35% based on satisfaction</p>
                    </div>
                  </div>

                  <div className="info-card">
                    <div className="info-icon">
                      <span className="emoji-visible">🚗</span>
                    </div>
                    <div className="info-content">
                      <h5>Travel Policy</h5>
                      <p>
                        Free {displayFreeMiles} mi, ${displayPerMileRate}/mi after
                      </p>
                    </div>
                  </div>
                </div>

                <div className="alert alert-info mt-4">
                  <i className="bi bi-info-circle-fill me-2"></i>
                  All packages include fried rice, mixed vegetables, and our signature sauces.
                </div>
              </div>
            </div>
          </div>

          {/* What's Included Section */}
          <div className="card menu-card mb-5 overflow-hidden border-0 p-0">
            <div className="included-section compact-included p-5">
              <div className="mb-5 text-center">
                <div className="section-header animated-section">
                  <div className="section-icon-wrapper mb-3">
                    <span className="section-icon emoji-visible">🍽️</span>
                  </div>
                  <h2 className="section-title mb-4">Complete Hibachi Experience</h2>
                  <p className="section-subtitle">
                    Every booking includes these delicious accompaniments & entertainment
                  </p>
                </div>
              </div>

              <CenteredFlexGrid className="included-items-grid mb-4" itemMinWidth={280} gap={12}>
                <div className="included-item modern-item enhanced-item">
                  <div className="item-icon-wrapper">
                    <span className="included-icon emoji-visible">🍚</span>
                  </div>
                  <div className="included-content">
                    <h5 className="included-title">Hibachi Fried Rice</h5>
                    <p className="included-desc">
                      Perfectly seasoned with fresh eggs and mixed vegetables
                    </p>
                    <div className="included-badge">Signature Recipe</div>
                  </div>
                </div>

                <div className="included-item modern-item enhanced-item">
                  <div className="item-icon-wrapper">
                    <span className="included-icon emoji-visible">🥬</span>
                  </div>
                  <div className="included-content">
                    <h5 className="included-title">Fresh Seasonal Vegetables</h5>
                    <p className="included-desc">
                      Zucchini, carrots, onions, mushrooms, and broccoli
                    </p>
                    <div className="included-badge">Farm Fresh</div>
                  </div>
                </div>

                <div className="included-item modern-item enhanced-item">
                  <div className="item-icon-wrapper">
                    <span className="included-icon emoji-visible">🥗</span>
                  </div>
                  <div className="included-content">
                    <h5 className="included-title">Garden Fresh Salad</h5>
                    <p className="included-desc">Crisp greens with our signature ginger dressing</p>
                    <div className="included-badge">House Special</div>
                  </div>
                </div>

                <div className="included-item modern-item enhanced-item">
                  <div className="item-icon-wrapper">
                    <span className="included-icon emoji-visible">🥄</span>
                  </div>
                  <div className="included-content">
                    <h5 className="included-title">Famous Yum Yum Sauce</h5>
                    <p className="included-desc">Our legendary creamy signature sauce</p>
                    <div className="included-badge">Customer Favorite</div>
                  </div>
                </div>

                <div className="included-item modern-item enhanced-item">
                  <div className="item-icon-wrapper">
                    <span className="included-icon emoji-visible">🌶️</span>
                  </div>
                  <div className="included-content">
                    <h5 className="included-title">House Special Hot Sauce</h5>
                    <p className="included-desc">
                      Bold and spicy signature blend with perfect heat
                    </p>
                    <div className="included-badge">Chef&apos;s Special</div>
                  </div>
                </div>

                <div className="included-item modern-item enhanced-item">
                  <div className="item-icon-wrapper">
                    <span className="included-icon emoji-visible">🎪</span>
                  </div>
                  <div className="included-content">
                    <h5 className="included-title">Live Chef Entertainment</h5>
                    <p className="included-desc">
                      Amazing tricks, flips, and interactive cooking show
                    </p>
                    <div className="included-badge">Unforgettable</div>
                  </div>
                </div>
              </CenteredFlexGrid>

              <div className="protein-selection-banner modern-banner enhanced-banner">
                <div className="banner-content">
                  <div className="banner-icon">
                    <span className="emoji-visible">🥩</span>
                  </div>
                  <div className="banner-text">
                    <h3 className="banner-title">Choose Any 2 Proteins From Below</h3>
                    <p className="banner-subtitle">
                      Mix and match for the perfect combination that suits your taste
                    </p>
                  </div>
                  <div className="banner-decoration">
                    <span className="emoji-visible">🍤</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Enhanced Protein Options and Premium Upgrades - Collapsible */}
          <div className="card menu-card mb-5 overflow-hidden border-0 p-0">
            <div className="proteins-section p-5">
              {/* Collapsible Header with Toggle */}
              <button
                onClick={() => setIsProteinsOpen(!isProteinsOpen)}
                className="collapsible-header w-full"
                aria-expanded={isProteinsOpen}
              >
                <div className="collapsible-header-content">
                  <div className="collapsible-icons">
                    <span className="emoji-visible">🥩</span>
                    <span className="emoji-visible">🍤</span>
                  </div>
                  <div className="collapsible-text">
                    <h2 className="collapsible-title">Protein Selection</h2>
                    <p className="collapsible-subtitle">
                      Choose your perfect combination from our premium selection
                    </p>
                  </div>
                  <div className="collapsible-toggle">
                    <span className="toggle-text">{isProteinsOpen ? 'Hide' : 'View Options'}</span>
                    {isProteinsOpen ? (
                      <ChevronUp className="toggle-icon" />
                    ) : (
                      <ChevronDown className="toggle-icon" />
                    )}
                  </div>
                </div>
              </button>

              {/* Collapsible Content */}
              <div className={`collapsible-content ${isProteinsOpen ? 'open' : ''}`}>
                <div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
                  <div className="mb-4">
                    <div className="protein-card modern-card enhanced-protein-card">
                      <div className="card-glow"></div>
                      <div className="card-header enhanced-header">
                        <div className="card-icon-wrapper">
                          <span className="card-icon emoji-visible">✅</span>
                        </div>
                        <div className="header-content">
                          <h3 className="card-title">Base Protein Options</h3>
                          <p className="card-subtitle">Choose any 2 - Included in every meal</p>
                        </div>
                        <div className="included-badge pulse-badge">
                          <span className="emoji-visible">🆓</span>
                          Included
                        </div>
                      </div>
                      <div className="card-body enhanced-body">
                        <div className="protein-item modern-protein-item enhanced-protein-item">
                          <div className="protein-content">
                            <div className="protein-header">
                              <h5 className="protein-name">Chicken</h5>
                              <div className="protein-sparkle">
                                <span className="emoji-visible">✨</span>
                              </div>
                            </div>
                            <p className="protein-desc">
                              Tender grilled chicken breast with signature hibachi seasonings and
                              teriyaki glaze
                            </p>
                            <div className="protein-features">
                              <span className="feature-tag">Fresh Daily</span>
                              <span className="feature-tag">Chef&apos;s Choice</span>
                            </div>
                          </div>
                          <div className="protein-check">
                            <div className="check-circle">
                              <span className="check-icon">✓</span>
                            </div>
                          </div>
                        </div>

                        <div className="protein-item modern-protein-item enhanced-protein-item">
                          <div className="protein-content">
                            <div className="protein-header">
                              <h5 className="protein-name">NY Strip Steak</h5>
                              <div className="protein-sparkle">
                                <span className="emoji-visible">✨</span>
                              </div>
                            </div>
                            <p className="protein-desc">
                              Premium NY strip steak cooked to your preferred temperature
                            </p>
                            <div className="protein-features">
                              <span className="feature-tag">Fresh Daily</span>
                              <span className="feature-tag">Chef&apos;s Choice</span>
                            </div>
                          </div>
                          <div className="protein-check">
                            <div className="check-circle">
                              <span className="check-icon">✓</span>
                            </div>
                          </div>
                        </div>

                        <div className="protein-item modern-protein-item enhanced-protein-item">
                          <div className="protein-content">
                            <div className="protein-header">
                              <h5 className="protein-name">Shrimp</h5>
                              <div className="protein-sparkle">
                                <span className="emoji-visible">✨</span>
                              </div>
                            </div>
                            <p className="protein-desc">
                              Fresh jumbo shrimp with garlic butter and hibachi spices
                            </p>
                            <div className="protein-features">
                              <span className="feature-tag">Fresh Daily</span>
                              <span className="feature-tag">Chef&apos;s Choice</span>
                            </div>
                          </div>
                          <div className="protein-check">
                            <div className="check-circle">
                              <span className="check-icon">✓</span>
                            </div>
                          </div>
                        </div>

                        <div className="protein-item modern-protein-item enhanced-protein-item">
                          <div className="protein-content">
                            <div className="protein-header">
                              <h5 className="protein-name">Calamari</h5>
                              <div className="protein-sparkle">
                                <span className="emoji-visible">✨</span>
                              </div>
                            </div>
                            <p className="protein-desc">
                              Fresh tender calamari grilled with garlic and hibachi spices
                            </p>
                            <div className="protein-features">
                              <span className="feature-tag">Fresh Daily</span>
                              <span className="feature-tag">Chef&apos;s Choice</span>
                            </div>
                          </div>
                          <div className="protein-check">
                            <div className="check-circle">
                              <span className="check-icon">✓</span>
                            </div>
                          </div>
                        </div>

                        <div className="protein-item modern-protein-item enhanced-protein-item">
                          <div className="protein-content">
                            <div className="protein-header">
                              <h5 className="protein-name">Tofu</h5>
                              <div className="protein-sparkle">
                                <span className="emoji-visible">✨</span>
                              </div>
                            </div>
                            <p className="protein-desc">
                              Fried tofu with our house special seasoning - perfect vegetarian
                              option
                            </p>
                            <div className="protein-features">
                              <span className="feature-tag">Fresh Daily</span>
                              <span className="feature-tag">Chef&apos;s Choice</span>
                            </div>
                          </div>
                          <div className="protein-check">
                            <div className="check-circle">
                              <span className="check-icon">✓</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mb-4">
                    <div className="upgrade-card modern-card featured-upgrade enhanced-upgrade-card">
                      <div className="card-glow premium-glow"></div>
                      <div className="card-header enhanced-header premium-header">
                        <div className="card-icon-wrapper premium-icon">
                          <span className="card-icon emoji-visible">⭐</span>
                        </div>
                        <div className="header-content">
                          <h3 className="card-title">Premium Upgrades</h3>
                          <p className="card-subtitle">
                            Replace any protein with these premium options
                          </p>
                        </div>
                        <div className="upgrade-badge premium-badge">
                          <span className="emoji-visible">💎</span>
                          Premium
                        </div>
                      </div>
                      <div className="card-body enhanced-body">
                        <div className="upgrade-item modern-upgrade-item enhanced-upgrade-item">
                          <div className="upgrade-content">
                            <div className="upgrade-header">
                              <h5 className="upgrade-name">Salmon</h5>
                              <div className="popular-badge">
                                <span className="emoji-visible">🔥</span>
                                <span>Popular</span>
                              </div>
                            </div>
                            <p className="upgrade-desc">
                              Wild-caught Atlantic salmon with teriyaki glaze
                            </p>
                            <div className="upgrade-features">
                              <span className="feature-tag premium-tag">Premium Quality</span>
                              <span className="feature-tag premium-tag">Fresh Daily</span>
                            </div>
                          </div>
                          <div className="upgrade-price">
                            <div className="price-circle enhanced-price-circle">
                              <span className="price-tag">+${displaySalmonPrice}</span>
                              <span className="price-label">per person</span>
                            </div>
                          </div>
                        </div>

                        <div className="upgrade-item modern-upgrade-item enhanced-upgrade-item">
                          <div className="upgrade-content">
                            <div className="upgrade-header">
                              <h5 className="upgrade-name">Scallops</h5>
                              <div className="popular-badge">
                                <span className="emoji-visible">🔥</span>
                                <span>Popular</span>
                              </div>
                            </div>
                            <p className="upgrade-desc">Fresh sea scallops grilled to perfection</p>
                            <div className="upgrade-features">
                              <span className="feature-tag premium-tag">Premium Quality</span>
                              <span className="feature-tag premium-tag">Fresh Daily</span>
                            </div>
                          </div>
                          <div className="upgrade-price">
                            <div className="price-circle enhanced-price-circle">
                              <span className="price-tag">+${displayScallopsPrice}</span>
                              <span className="price-label">per person</span>
                            </div>
                          </div>
                        </div>

                        <div className="upgrade-item modern-upgrade-item enhanced-upgrade-item">
                          <div className="upgrade-content">
                            <div className="upgrade-header">
                              <h5 className="upgrade-name">Filet Mignon</h5>
                              <div className="popular-badge">
                                <span className="emoji-visible">🔥</span>
                                <span>Popular</span>
                              </div>
                            </div>
                            <p className="upgrade-desc">Premium tender beef filet</p>
                            <div className="upgrade-features">
                              <span className="feature-tag premium-tag">Premium Quality</span>
                              <span className="feature-tag premium-tag">Fresh Daily</span>
                            </div>
                          </div>
                          <div className="upgrade-price">
                            <div className="price-circle enhanced-price-circle">
                              <span className="price-tag">+${displayFiletPrice}</span>
                              <span className="price-label">per person</span>
                            </div>
                          </div>
                        </div>

                        <div className="upgrade-item modern-upgrade-item enhanced-upgrade-item">
                          <div className="upgrade-content">
                            <div className="upgrade-header">
                              <h5 className="upgrade-name">Lobster Tail</h5>
                              <div className="luxury-badge">
                                <span className="emoji-visible">👑</span>
                                <span>Luxury</span>
                              </div>
                            </div>
                            <p className="upgrade-desc">Fresh lobster tail with garlic butter</p>
                            <div className="upgrade-features">
                              <span className="feature-tag premium-tag">Premium Quality</span>
                              <span className="feature-tag premium-tag">Fresh Daily</span>
                            </div>
                          </div>
                          <div className="upgrade-price">
                            <div className="price-circle enhanced-price-circle">
                              <span className="price-tag">+${displayLobsterPrice}</span>
                              <span className="price-label">per person</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Modern Additional Options - Collapsible */}
          <div className="card menu-card mb-5 overflow-hidden border-0 p-0">
            <div className="additional-section p-5">
              {/* Collapsible Header with Toggle */}
              <button
                onClick={() => setIsAdditionsOpen(!isAdditionsOpen)}
                className="collapsible-header w-full"
                aria-expanded={isAdditionsOpen}
              >
                <div className="collapsible-header-content">
                  <div className="collapsible-icons">
                    <span className="emoji-visible">🍜</span>
                    <span className="emoji-visible">✨</span>
                  </div>
                  <div className="collapsible-text">
                    <h2 className="collapsible-title">Additional Enhancements</h2>
                    <p className="collapsible-subtitle">
                      Take your hibachi experience to the next level
                    </p>
                  </div>
                  <div className="collapsible-toggle">
                    <span className="toggle-text">{isAdditionsOpen ? 'Hide' : 'View Options'}</span>
                    {isAdditionsOpen ? (
                      <ChevronUp className="toggle-icon" />
                    ) : (
                      <ChevronDown className="toggle-icon" />
                    )}
                  </div>
                </div>
              </button>

              {/* Collapsible Content */}
              <div className={`collapsible-content ${isAdditionsOpen ? 'open' : ''}`}>
                <div className="additional-items-grid">
                  <div className="additional-item-card modern-additional-card">
                    <div className="additional-content">
                      <div className="additional-icon-wrapper">
                        <span className="additional-icon emoji-visible">🍜</span>
                      </div>
                      <h5 className="additional-name">Yakisoba Noodles</h5>
                      <p className="additional-desc">Japanese style lo mein noodles</p>
                    </div>
                    <div className="additional-price">
                      <div className="add-price-circle">
                        <span className="add-price-tag">+${displayYakisobaPrice}</span>
                      </div>
                    </div>
                  </div>

                  <div className="additional-item-card modern-additional-card">
                    <div className="additional-content">
                      <div className="additional-icon-wrapper">
                        <span className="additional-icon emoji-visible">🍚</span>
                      </div>
                      <h5 className="additional-name">Extra Fried Rice</h5>
                      <p className="additional-desc">Additional portion of hibachi fried rice</p>
                    </div>
                    <div className="additional-price">
                      <div className="add-price-circle">
                        <span className="add-price-tag">+${displayExtraRicePrice}</span>
                      </div>
                    </div>
                  </div>

                  <div className="additional-item-card modern-additional-card">
                    <div className="additional-content">
                      <div className="additional-icon-wrapper">
                        <span className="additional-icon emoji-visible">🥬</span>
                      </div>
                      <h5 className="additional-name">Extra Vegetables</h5>
                      <p className="additional-desc">
                        Additional portion of mixed seasonal vegetables
                      </p>
                    </div>
                    <div className="additional-price">
                      <div className="add-price-circle">
                        <span className="add-price-tag">+${displayExtraVeggiesPrice}</span>
                      </div>
                    </div>
                  </div>

                  <div className="additional-item-card modern-additional-card">
                    <div className="additional-content">
                      <div className="additional-icon-wrapper">
                        <span className="additional-icon emoji-visible">🫛</span>
                      </div>
                      <h5 className="additional-name">Edamame</h5>
                      <p className="additional-desc">Fresh steamed soybeans with sea salt</p>
                    </div>
                    <div className="additional-price">
                      <div className="add-price-circle">
                        <span className="add-price-tag">+${displayEdamamePrice}</span>
                      </div>
                    </div>
                  </div>

                  <div className="additional-item-card modern-additional-card">
                    <div className="additional-content">
                      <div className="additional-icon-wrapper">
                        <span className="additional-icon emoji-visible">🥟</span>
                      </div>
                      <h5 className="additional-name">Gyoza</h5>
                      <p className="additional-desc">Pan-fried Japanese dumplings</p>
                    </div>
                    <div className="additional-price">
                      <div className="add-price-circle">
                        <span className="add-price-tag">+${displayGyozaPrice}</span>
                      </div>
                    </div>
                  </div>

                  <div className="additional-item-card modern-additional-card">
                    <div className="additional-content">
                      <div className="additional-icon-wrapper">
                        <span className="additional-icon emoji-visible">🥩</span>
                      </div>
                      <h5 className="additional-name">Extra Protein</h5>
                      <p className="additional-desc">Add an extra protein to your meal</p>
                    </div>
                    <div className="additional-price">
                      <div className="add-price-circle">
                        <span className="add-price-tag">+${displayExtraProteinPrice}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Call to Action */}
      <div className="container-fluid px-lg-5 mb-4">
        <div className="card menu-card overflow-hidden border-0 p-0">
          <div className="cta-section compact-cta p-4 text-center">
            <div className="cta-content-wrapper">
              <div className="cta-background-pattern"></div>

              {/* CTA Header */}
              <div className="cta-header mb-3">
                <div className="cta-icon-group mb-3">
                  <span className="cta-icon emoji-visible floating-cta-icon">🍽️</span>
                  <span className="cta-icon emoji-visible floating-cta-icon">🎉</span>
                  <span className="cta-icon emoji-visible floating-cta-icon">👨‍🍳</span>
                </div>
                <h2 className="cta-main-title">Ready for an Unforgettable Experience?</h2>
                <p className="cta-main-subtitle">
                  Book your premium hibachi experience today and create memories that will last a
                  lifetime
                </p>
              </div>

              {/* Main CTA Button */}
              <div className="cta-button-wrapper mb-3">
                <Link
                  href="/book-us/"
                  aria-label="Order your hibachi experience now"
                  className="cta-link"
                >
                  <button className="cta-main-button modern-cta-button">
                    <span className="button-icon emoji-visible">🍽️</span>
                    <span className="button-text">Order Your Hibachi Experience</span>
                    <span className="button-icon emoji-visible">🍽️</span>
                    <div className="button-shimmer"></div>
                  </button>
                </Link>

                {/* Secondary actions */}
                <div className="secondary-actions mt-3">
                  <div className="action-item">
                    <span className="emoji-visible">📞</span>
                    <span>Call for custom packages</span>
                  </div>
                  <div className="action-divider">•</div>
                  <div className="action-item">
                    <span className="emoji-visible">💬</span>
                    <span>Ask about group discounts</span>
                  </div>
                </div>
              </div>

              {/* Enhanced Feature Highlights */}
              <div className="cta-features-section">
                <h3 className="features-title mb-3">Why Choose My Hibachi?</h3>
                <div className="cta-features-grid">
                  <div className="cta-feature-card modern-feature-card">
                    <div className="feature-icon-wrapper">
                      <span className="feature-icon emoji-visible">👨‍🍳</span>
                    </div>
                    <div className="feature-content">
                      <h4 className="feature-title">Professional Chef</h4>
                      <p className="feature-description">
                        Highly trained hibachi chefs delivering exceptional on-site dining
                        experiences with skill, flair, and passion
                      </p>
                    </div>
                  </div>

                  <div className="cta-feature-card modern-feature-card">
                    <div className="feature-icon-wrapper">
                      <span className="feature-icon emoji-visible">🎭</span>
                    </div>
                    <div className="feature-content">
                      <h4 className="feature-title">Live Entertainment</h4>
                      <p className="feature-description">
                        Amazing tricks, flips, and interactive cooking show
                      </p>
                    </div>
                  </div>

                  <div className="cta-feature-card modern-feature-card">
                    <div className="feature-icon-wrapper">
                      <span className="feature-icon emoji-visible">🎯</span>
                    </div>
                    <div className="feature-content">
                      <h4 className="feature-title">Personalized Service</h4>
                      <p className="feature-description">
                        Customized experience tailored to your preferences
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
