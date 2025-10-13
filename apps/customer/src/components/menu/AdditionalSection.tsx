import { menuData } from '@/data/menu'
import styles from '@/styles/menu/additional.module.css'

export default function AdditionalSection() {
  const { additionalServices } = menuData

  return (
    <div className={styles.additionalCard}>
      <div className={styles.additionalSection}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionIconWrapper}>
            <span className={`${styles.sectionIcon} emoji-visible`}>✨</span>
          </div>
          <h2 className={styles.sectionTitle}>{additionalServices.title}</h2>
          <p className={styles.sectionSubtitle}>{additionalServices.subtitle}</p>
        </div>

        <div className={styles.servicesGrid}>
          {additionalServices.items.map((service: any, index: number) => (
            <div key={index} className={styles.serviceItem}>
              <div className={styles.serviceHeader}>
                <h3 className={styles.serviceName}>{service.name}</h3>
                <div className={styles.servicePrice}>{service.price}</div>
              </div>
              <p className={styles.serviceDescription}>{service.description}</p>
            </div>
          ))}
        </div>

        <div className={styles.addOnNote}>
          <p>
            <span className="emoji-visible">💡</span>
            <strong>Add-On Services:</strong> These optional services can be added to any package.
            Discuss your preferences when booking to create the perfect experience.
          </p>
        </div>
      </div>
    </div>
  )
}
