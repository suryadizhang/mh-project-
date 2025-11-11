import { menuData } from '@/data/menu'
import styles from '@/styles/menu/pricing.module.css'

export default function PricingSection() {
  const { pricing } = menuData

  return (
    <div className={styles.pricingCard}>
      <div className={styles.pricingSection}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionIconWrapper}>
            <span className={`${styles.sectionIcon} emoji-visible`}>💰</span>
          </div>
          <h2 className={styles.sectionTitle}>
            <span>{pricing.title}</span>
          </h2>
          <p className={styles.sectionSubtitle}>{pricing.subtitle}</p>
        </div>

        <div className={styles.pricingGrid}>
          {pricing.tiers.map((tier: any) => (
            <div
              key={tier.id}
              className={`${styles.pricingTier} ${tier.popular ? styles.popularTier : ''}`}
            >
              {tier.popular && (
                <div className={styles.popularBadge}>
                  <span className="emoji-visible">⭐</span> Most Popular
                </div>
              )}

              <div className={styles.tierHeader}>
                <h3 className={styles.tierName}>{tier.name}</h3>
                <div className={styles.tierPrice}>
                  {tier.price}
                  <span className={styles.priceUnit}>/person</span>
                </div>
                <p className={styles.tierDescription}>{tier.description}</p>
                <p className={styles.minGuests}>Minimum {tier.minGuests} guests</p>
              </div>

              <div className={styles.tierFeatures}>
                {tier.features.map((feature: any, index: number) => (
                  <div key={index} className={styles.feature}>
                    <span className={`${styles.featureIcon} emoji-visible`}>✓</span>
                    <span>{feature}</span>
                  </div>
                ))}
              </div>

              <div className={styles.tierCta}>
                <a href="/BookUs" className={styles.ctaButton}>
                  Choose This Package
                </a>
              </div>
            </div>
          ))}
        </div>

        <div className={styles.pricingNote}>
          <p>
            <span className="emoji-visible">💡</span>
            <strong>Note:</strong> Prices are per person. All packages include professional chef,
            equipment, and entertainment. Travel fees may apply outside primary service areas.
          </p>
        </div>
      </div>
    </div>
  )
}
