import { Calculator, Calendar, MessageCircle } from 'lucide-react'
import styles from '@/styles/menu/cta.module.css'

export default function CTASection() {
  return (
    <div className={styles.ctaSection}>
      <div className={styles.ctaContent}>
        <h2 className={styles.ctaTitle}>Ready to Book Your Hibachi Experience?</h2>
        <p className={styles.ctaSubtitle}>
          Join thousands of satisfied customers who&apos;ve made their events unforgettable with My Hibachi!
        </p>
        
        <div className={styles.ctaButtons}>
          <a href="/BookUs" className={styles.primaryCtaButton}>
            <Calendar className={styles.buttonIcon} />
            Book Your Event Now
          </a>
          <a href="/quote" className={styles.secondaryCtaButton}>
            <Calculator className={styles.buttonIcon} />
            Get Custom Quote
          </a>
          <a href="/contact" className={styles.tertiaryCtaButton}>
            <MessageCircle className={styles.buttonIcon} />
            Ask Questions
          </a>
        </div>
        
        <div className={styles.trustSignals}>
          <div className={styles.trustItem}>
            <span className={`${styles.trustIcon} emoji-visible`}>⭐</span>
            <span>500+ Happy Events</span>
          </div>
          <div className={styles.trustItem}>
            <span className={`${styles.trustIcon} emoji-visible`}>🏆</span>
            <span>Premium Quality</span>
          </div>
          <div className={styles.trustItem}>
            <span className={`${styles.trustIcon} emoji-visible`}>🎯</span>
            <span>100% Satisfaction</span>
          </div>
        </div>
      </div>
    </div>
  )
}
