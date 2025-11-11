import { menuData } from '@/data/menu'
import styles from '@/styles/menu/proteins.module.css'

export default function ProteinsSection() {
  const { proteins } = menuData

  return (
    <div className={styles.proteinsCard}>
      <div className={styles.proteinsSection}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionIconWrapper}>
            <span className={`${styles.sectionIcon} emoji-visible`}>🥩</span>
          </div>
          <h2 className={styles.sectionTitle}>{proteins.title}</h2>
          <p className={styles.sectionSubtitle}>{proteins.subtitle}</p>
        </div>

        <div className={styles.proteinsGrid}>
          {proteins.categories.map((category: any, index: number) => (
            <div key={index} className={styles.proteinCategory}>
              <h3 className={styles.categoryTitle}>{category.name}</h3>
              <div className={styles.proteinItems}>
                {category.items.map((item: any, itemIndex: number) => (
                  <div key={itemIndex} className={styles.proteinItem}>
                    <div className={styles.proteinName}>{item.name}</div>
                    <div className={styles.proteinDescription}>{item.description}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className={styles.proteinNote}>
          <p>
            <span className="emoji-visible">👨‍🍳</span>
            <strong>Chef&apos;s Note:</strong> All proteins are fresh, never frozen, and prepared
            with our signature seasonings. Special dietary requirements can be accommodated with
            advance notice.
          </p>
        </div>
      </div>
    </div>
  )
}
