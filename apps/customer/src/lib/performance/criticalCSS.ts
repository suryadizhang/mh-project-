/**
 * Critical CSS for Above-the-Fold Content
 * This CSS is inlined directly in the HTML to eliminate render-blocking
 * Only includes styles needed for initial paint (hero section)
 */
export const criticalCSS = `
/* Base resets needed for LCP */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { line-height: 1.5; -webkit-text-size-adjust: 100%; }
body { font-family: var(--font-inter), system-ui, -apple-system, sans-serif; }
img, video { max-width: 100%; height: auto; display: block; }

/* Hero Section - Critical for LCP */
[data-page='home'] { width: 100%; display: block; }
.about-section { position: relative; padding-top: 0; overflow: hidden; }
.hero-media-container { position: relative; width: 100%; height: 480px; overflow: hidden; margin-bottom: 2rem; }
.hero-media-overlay { position: absolute; inset: 0; background: rgb(0 0 0 / 50%); z-index: 1; }
.hero-media { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.hero-video { z-index: 0; }

/* Headline - visible immediately after hero */
.headline-section { position: relative; z-index: 2; margin-top: -120px; padding: 1.5rem; text-align: center; }
.main-title { font-family: var(--font-poppins), system-ui, sans-serif; font-size: clamp(1.75rem, 5vw, 3rem); font-weight: 700; color: #fff; text-shadow: 2px 2px 4px rgb(0 0 0 / 50%); margin-bottom: 0.75rem; }
.subtitle { font-size: clamp(1rem, 2.5vw, 1.25rem); color: #fff; text-shadow: 1px 1px 2px rgb(0 0 0 / 50%); margin-bottom: 1rem; }
.quality-badge { display: inline-block; background: linear-gradient(135deg, #b91c1c, #dc2626); color: #fff; padding: 0.5rem 1rem; border-radius: 9999px; font-size: 0.875rem; font-weight: 600; }

/* Mobile-first responsive */
@media (max-width: 768px) {
  .hero-media-container { height: 300px; }
  .headline-section { margin-top: -80px; padding: 1rem; }
}
`;

/**
 * Get critical CSS as a style tag for SSR
 */
export function getCriticalStyleTag(): string {
  return `<style id="critical-css">${criticalCSS}</style>`;
}
