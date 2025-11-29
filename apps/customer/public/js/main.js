// Main JavaScript for interactive features

// Scroll animations
function handleScrollAnimations() {
  const animatedElements = document.querySelectorAll('.animate-on-scroll')

  const observer = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible')
        }
      })
    },
    {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    }
  )

  animatedElements.forEach(element => {
    observer.observe(element)
  })
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
  handleScrollAnimations()
})

// Handle animations on route changes for Next.js
if (typeof window !== 'undefined') {
  // Re-initialize animations when navigating in Next.js
  const originalPushState = history.pushState
  const originalReplaceState = history.replaceState

  history.pushState = function () {
    originalPushState.apply(history, arguments)
    setTimeout(handleScrollAnimations, 100)
  }

  history.replaceState = function () {
    originalReplaceState.apply(history, arguments)
    setTimeout(handleScrollAnimations, 100)
  }

  window.addEventListener('popstate', function () {
    setTimeout(handleScrollAnimations, 100)
  })
}

export { handleScrollAnimations }
