import { menuData } from '@/data/menu'
import styles from '@/styles/menu/hero.module.css'

export default function MenuHero() {
  const { hero } = menuData

  return (
    <div className={styles.heroSection}>
      <div className={styles.heroContent}>
        <div className={styles.heroIconWrapper}>
          <div className={styles.floatingIcons}>
            <span className={`${styles.heroMainIcon} emoji-visible`}>🍱</span>
            <span
              className={`${styles.floatingIcon} emoji-visible`}
              style={{ animationDelay: '0s' }}
            >
              🔥
            </span>
            <span
              className={`${styles.floatingIcon} emoji-visible`}
              style={{ animationDelay: '1s' }}
            >
              🥢
            </span>
            <span
              className={`${styles.floatingIcon} emoji-visible`}
              style={{ animationDelay: '2s' }}
            >
              🍤
            </span>
            <span
              className={`${styles.floatingIcon} emoji-visible`}
              style={{ animationDelay: '3s' }}
            >
              🥩
            </span>
          </div>
        </div>

        <h1 className={styles.heroTitle}>
          <span className={styles.gradientText}>{hero.title}</span>
        </h1>

        <p className={styles.heroSubtitle}>
          <span className="emoji-visible">✨</span>
          {hero.subtitle}
          <span className="emoji-visible">✨</span>
        </p>

        {/* Value Proposition */}
        <div className={styles.valueProposition}>
          {hero.valueProposition.map((item, index) => (
            <div key={index}>
              <div className={styles.valueItem}>
                <span className={`${styles.valueIcon} emoji-visible`}>{item.icon}</span>
                <span className={styles.valueText}>{item.text}</span>
              </div>
              {index < hero.valueProposition.length - 1 && (
                <div className={styles.valueDivider}>•</div>
              )}
            </div>
          ))}
        </div>

        {/* Feature badges */}
        <div className={styles.heroFeaturesGrid}>
          {hero.features.map((feature: any, index: number) => (
            <div key={index} className={styles.featureBadge}>
              <div className={styles.featureIconBg}>
                <span className={`${styles.featureIcon} emoji-visible`}>{feature.icon}</span>
              </div>
              <div className={styles.featureContent}>
                <span className={styles.featureTitle}>{feature.title}</span>
                <span className={styles.featureSubtitle}>{feature.subtitle}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
