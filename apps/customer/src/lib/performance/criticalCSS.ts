/**
 * Critical CSS for Above-the-Fold Content
 * This CSS is inlined directly in the HTML to eliminate render-blocking
 * Includes: Base resets, Navbar, Hero section, Headline
 *
 * IMPORTANT: Keep in sync with actual component styles
 * Last updated: 2024-12-17
 */
export const criticalCSS = `
/* ========== Base Resets ========== */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { line-height: 1.5; -webkit-text-size-adjust: 100%; }
body { 
  font-family: var(--font-inter), system-ui, -apple-system, sans-serif;
  background-color: #f9e8d0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
img, video { max-width: 100%; height: auto; display: block; }
a { text-decoration: none; color: inherit; }
ul, ol { list-style: none; }

/* ========== CSS Variables (Essential) ========== */
:root {
  --font-inter: 'Inter', system-ui, sans-serif;
  --font-poppins: 'Poppins', system-ui, sans-serif;
  --color-primary: #dc2626;
  --color-primary-hover: #b91c1c;
  --color-neutral-100: #f9e8d0;
}

/* ========== Navbar (Above-the-fold) ========== */
nav[class*="navbar"] {
  position: sticky !important;
  top: 0 !important;
  z-index: 1020 !important;
  background: #f9e8d0 !important;
  box-shadow: 0 4px 20px rgb(0 0 0 / 10%);
  border-bottom: 2px solid rgba(220, 38, 38, 0.1);
  padding: 1rem 0;
}

nav[class*="navbar"] > div[class*="container"] {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

nav a[class*="brand"] {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

nav img[class*="logo"] {
  height: auto;
  width: auto;
  max-height: 80px;
}

nav span[class*="brandText"] {
  color: #dc2626;
  font-size: 1.25rem;
  font-weight: 700;
}

nav ul[class*="navList"] {
  display: flex !important;
  align-items: center;
  gap: 0.25rem;
}

nav a[class*="navLink"] {
  color: #1f2937 !important;
  font-weight: 500;
  padding: 0.75rem 1rem !important;
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  white-space: nowrap;
}

nav button[class*="toggler"] {
  display: none;
  border: none;
  padding: 0.75rem;
  min-width: 48px;
  min-height: 48px;
  border-radius: 0.5rem;
  background-color: rgba(220, 38, 38, 0.1);
  cursor: pointer;
}

/* ========== Hero Section ========== */
[data-page='home'] { width: 100%; display: block; }

.about-section {
  position: relative;
  padding-top: 0;
  overflow: hidden;
}

.hero-media-container {
  position: relative;
  width: 100%;
  height: 480px;
  overflow: hidden;
  margin-bottom: 2rem;
}

.hero-media-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgb(0 0 0 / 50%);
  z-index: 1;
}

.hero-media {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hero-video { z-index: 0; }

/* ========== Headline Section ========== */
.headline-section {
  position: relative;
  z-index: 2;
  color: white;
  text-align: center;
  margin-top: -380px;
  margin-bottom: 40px;
  padding: 1.5rem;
  background: rgb(0 0 0 / 40%);
  border-radius: 12px;
  backdrop-filter: blur(5px);
}

.main-title {
  font-family: var(--font-poppins), system-ui, sans-serif;
  font-size: 3.5rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
  text-shadow: 3px 3px 15px rgb(0 0 0 / 90%), 0 0 25px rgb(0 0 0 / 80%);
  background: linear-gradient(to right, #fff, #f8e3bb, #fff);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  display: inline-block;
}

.subtitle {
  font-size: 1.35rem;
  max-width: 750px;
  margin: 0 auto 1.5rem;
  text-shadow: 2px 2px 12px rgb(0 0 0 / 90%), 0 0 20px rgb(0 0 0 / 80%);
  color: white;
  font-weight: 500;
}

.quality-badge {
  display: inline-block;
  padding: 0.75rem 2rem;
  background: rgb(219 43 40 / 85%);
  color: white;
  font-weight: 500;
  border-radius: 50px;
  box-shadow: 0 4px 12px rgb(0 0 0 / 20%);
}

/* ========== Utility Classes (Tailwind-like) ========== */
.flex { display: flex; }
.flex-col { flex-direction: column; }
.min-h-screen { min-height: 100vh; }
.flex-1 { flex: 1 1 0%; }
.w-full { width: 100%; }
.antialiased { -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }
.text-center { text-align: center; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }
.company-background { background-color: #f9e8d0; }

/* ========== Mobile Responsive ========== */
@media (max-width: 991px) {
  nav button[class*="toggler"] { display: flex; align-items: center; justify-content: center; }
  nav div[class*="navCollapse"] { display: none !important; }
  nav div[class*="navCollapse"][class*="show"] { display: flex !important; }
  nav img[class*="logo"] { max-height: 60px; }
  nav span[class*="brandText"] { font-size: 1rem; }
}

@media (max-width: 768px) {
  .hero-media-container { height: 500px; }
  .headline-section { margin-top: -350px; margin-bottom: 50px; padding: 1.5rem; }
  .main-title { font-size: 2.5rem; }
  .subtitle { font-size: 1.2rem; }
  nav img[class*="logo"] { max-height: 50px; }
  nav span[class*="brandText"] { display: none; }
}

@media (max-width: 480px) {
  nav > div[class*="container"] { padding: 0 0.5rem; }
  nav img[class*="logo"] { max-height: 40px; }
}
`;

/**
 * Get critical CSS as a style tag for SSR
 */
export function getCriticalStyleTag(): string {
  return `<style id="critical-css">${criticalCSS}</style>`;
}
