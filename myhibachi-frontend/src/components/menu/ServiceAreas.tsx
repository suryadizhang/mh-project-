import { menuData } from '@/data/menu'
import styles from '@/styles/menu/service-areas.module.css'

export default function ServiceAreas() {
  const { serviceAreas } = menuData

  return (
    <div className={styles.serviceAreas}>
      <h3 className={styles.sectionTitle}>
        🌟 Bringing Hibachi Experience
        <br className="d-none d-lg-block" />
        to Your Neighborhood! 🌟
      </h3>
      <p className={styles.serviceIntro}>{serviceAreas.subtitle}</p>
      <div className={styles.ctaButtons}>
        <a href="/BookUs" className={styles.primaryBtn}>
          📅 Check Your Date & Time
        </a>
        <a href="/quote" className={styles.secondaryBtn}>
          💬 Get a Quick Quote
        </a>
      </div>

      <div className={styles.areasGrid}>
        <div className={styles.serviceAreaCard}>
          <h4 className={styles.areaTitle}>{serviceAreas.primary.title}</h4>
          <p className={styles.areaSubtitle}>{serviceAreas.primary.subtitle}</p>
          <ul className={styles.areaList}>
            {serviceAreas.primary.locations.map((location, index) => (
              <li key={index}>{location}</li>
            ))}
          </ul>
        </div>

        <div className={styles.serviceAreaCard}>
          <h4 className={styles.areaTitle}>{serviceAreas.extended.title}</h4>
          <p className={styles.areaSubtitle}>{serviceAreas.extended.subtitle}</p>
          <ul className={styles.areaList}>
            {serviceAreas.extended.locations.map((location, index) => (
              <li key={index}>{location}</li>
            ))}
          </ul>
        </div>
      </div>

      <div className={styles.travelNote}>
        <p>
          <span className="emoji-visible">🚗</span>
          <strong>Travel Policy:</strong> Free service within primary areas. Extended areas may
          include a small travel fee. Contact us for exact pricing for your location!
        </p>
      </div>
    </div>
  )
}
