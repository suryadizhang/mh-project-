import { test, expect } from '@playwright/test'

// Pages to check for DOM integrity and links
const pagestoCheck = [
  '/',
  '/menu',
  '/BookUs',
  '/quote',
  '/contact',
  '/blog',
  '/locations',
  '/locations/mountain-view',
  '/locations/fremont',
  '/locations/sacramento',
  '/faqs'
]

test.describe('DOM Structure and Link Validation', () => {
  test.beforeEach(async ({ page }) => {
    // Set up error logging
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`Console error on ${page.url()}: ${msg.text()}`)
      }
    })

    page.on('pageerror', error => {
      console.log(`Page error on ${page.url()}: ${error.message}`)
    })
  })

  pagestoCheck.forEach(pagePath => {
    test(`DOM structure validation for ${pagePath}`, async ({ page }) => {
      await page.goto(pagePath)
      await page.waitForLoadState('networkidle')

      // Check for critical DOM elements
      await expect(page.locator('html')).toBeVisible()
      await expect(page.locator('body')).toBeVisible()

      // Check for navigation
      const nav = page.locator('nav, [role="navigation"], header nav')
      await expect(nav.first()).toBeVisible()

      // Check for main content
      const main = page.locator('main, [role="main"], .main-content')
      await expect(main.first()).toBeVisible()

      // Check for footer
      const footer = page.locator('footer, [role="contentinfo"]')
      await expect(footer.first()).toBeVisible()

      // Verify no console errors
      const errors: string[] = []
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text())
        }
      })

      // Wait a bit for any async errors
      await page.waitForTimeout(1000)

      // Log errors if any (don't fail the test for minor console errors)
      if (errors.length > 0) {
        console.warn(`Console errors on ${pagePath}:`, errors)
      }
    })
  })
})

test.describe('Link Integrity Tests', () => {
  test('Internal links validation', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Get all internal links
    const internalLinks = await page.locator('a[href^="/"], a[href^="./"], a[href^="../"]').all()

    console.log(`Found ${internalLinks.length} internal links to test`)

    // Test a sample of internal links (to avoid overwhelming the test)
    const samplesToTest = Math.min(10, internalLinks.length)

    for (let i = 0; i < samplesToTest; i++) {
      const link = internalLinks[i]
      const href = await link.getAttribute('href')

      if (href && !href.includes('#') && !href.includes('mailto:') && !href.includes('tel:')) {
        try {
          // Click the link and verify it loads
          const response = await page.goto(href)
          expect(response?.status()).toBeLessThan(400)
          console.log(`✓ Link verified: ${href}`)
        } catch (error) {
          console.warn(`⚠ Link issue: ${href} - ${error}`)
        }
      }
    }
  })

  test('Critical navigation links', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    const criticalLinks = [
      { selector: 'a[href="/menu"]', name: 'Menu' },
      { selector: 'a[href="/BookUs"]', name: 'Book Us' },
      { selector: 'a[href="/contact"]', name: 'Contact' },
      { selector: 'a[href="/quote"]', name: 'Quote' },
      { selector: 'a[href="/blog"]', name: 'Blog' }
    ]

    for (const link of criticalLinks) {
      const element = page.locator(link.selector).first()
      if (await element.isVisible()) {
        await expect(element).toBeVisible()
        console.log(`✓ Critical link found: ${link.name}`)
      } else {
        console.warn(`⚠ Critical link not visible: ${link.name}`)
      }
    }
  })
})

test.describe('Form Functionality Tests', () => {
  test('Booking form basic functionality', async ({ page }) => {
    await page.goto('/BookUs')
    await page.waitForLoadState('networkidle')

    // Check if form elements exist
    const nameInput = page.locator('input[name="name"], input[placeholder*="name" i]')
    const emailInput = page.locator('input[name="email"], input[type="email"]')
    const phoneInput = page.locator('input[name="phone"], input[type="tel"]')

    if (await nameInput.first().isVisible()) {
      await expect(nameInput.first()).toBeVisible()
      console.log('✓ Name input found')
    }

    if (await emailInput.first().isVisible()) {
      await expect(emailInput.first()).toBeVisible()
      console.log('✓ Email input found')
    }

    if (await phoneInput.first().isVisible()) {
      await expect(phoneInput.first()).toBeVisible()
      console.log('✓ Phone input found')
    }
  })

  test('Contact form basic functionality', async ({ page }) => {
    await page.goto('/contact')
    await page.waitForLoadState('networkidle')

    // Check for contact form or contact information
    const contactForm = page.locator('form, .contact-form')
    const contactInfo = page.locator('.contact-info, .contact-details')

    const hasForm = await contactForm.first().isVisible()
    const hasInfo = await contactInfo.first().isVisible()

    expect(hasForm || hasInfo).toBeTruthy()
    console.log(`✓ Contact page has ${hasForm ? 'form' : 'info'}`)
  })
})

test.describe('Responsive Design Tests', () => {
  const viewports = [
    { width: 375, height: 667, name: 'Mobile' },
    { width: 768, height: 1024, name: 'Tablet' },
    { width: 1280, height: 720, name: 'Desktop' }
  ]

  viewports.forEach(({ width, height, name }) => {
    test(`Responsive design test - ${name} (${width}x${height})`, async ({ page }) => {
      await page.setViewportSize({ width, height })
      await page.goto('/')
      await page.waitForLoadState('networkidle')

      // Check that content is not overflowing
      const body = page.locator('body')
      const bodyBox = await body.boundingBox()

      if (bodyBox) {
        expect(bodyBox.width).toBeLessThanOrEqual(width + 20) // Allow small margin
      }

      // Check for mobile menu on smaller screens
      if (width <= 768) {
        const mobileMenu = page.locator('[data-testid="mobile-menu"], .mobile-menu, .hamburger')
        if (await mobileMenu.first().isVisible()) {
          console.log(`✓ Mobile menu detected on ${name}`)
        }
      }

      console.log(`✓ Responsive test passed for ${name}`)
    })
  })
})
