/**
 * Accessibility Utilities for Aegis Frontend
 * WCAG 2.1 AA Compliance helpers
 */

// Announce to screen readers
export function announceToScreenReader(message: string, priority: 'polite' | 'assertive' = 'polite') {
  const announcement = document.createElement('div')
  announcement.setAttribute('role', 'status')
  announcement.setAttribute('aria-live', priority)
  announcement.setAttribute('aria-atomic', 'true')
  announcement.className = 'sr-only'
  announcement.textContent = message

  document.body.appendChild(announcement)

  setTimeout(() => {
    document.body.removeChild(announcement)
  }, 1000)
}

// Handle keyboard navigation
export function handleKeyboardNavigation(event: KeyboardEvent, items: HTMLElement[], currentIndex: number) {
  let newIndex = currentIndex

  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault()
      newIndex = (currentIndex + 1) % items.length
      break
    case 'ArrowUp':
      event.preventDefault()
      newIndex = (currentIndex - 1 + items.length) % items.length
      break
    case 'Home':
      event.preventDefault()
      newIndex = 0
      break
    case 'End':
      event.preventDefault()
      newIndex = items.length - 1
      break
    default:
      return currentIndex
  }

  items[newIndex]?.focus()
  return newIndex
}

// Focus trap for modals
export function createFocusTrap(container: HTMLElement) {
  const focusableElements = container.querySelectorAll<HTMLElement>(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )

  const firstElement = focusableElements[0]
  const lastElement = focusableElements[focusableElements.length - 1]

  const handleTabKey = (event: KeyboardEvent) => {
    if (event.key !== 'Tab') return

    if (event.shiftKey) {
      if (document.activeElement === firstElement) {
        event.preventDefault()
        lastElement?.focus()
      }
    } else {
      if (document.activeElement === lastElement) {
        event.preventDefault()
        firstElement?.focus()
      }
    }
  }

  container.addEventListener('keydown', handleTabKey)

  // Focus first element
  firstElement?.focus()

  return () => {
    container.removeEventListener('keydown', handleTabKey)
  }
}

// Check if reduced motion is preferred
export function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

// Skip link for keyboard navigation
export function createSkipLink() {
  const skipLink = document.createElement('a')
  skipLink.href = '#main-content'
  skipLink.textContent = 'Skip to main content'
  skipLink.className = 'sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md'
  
  document.body.insertBefore(skipLink, document.body.firstChild)
}

// Generate unique IDs for ARIA relationships
let idCounter = 0
export function generateId(prefix: string = 'aegis'): string {
  idCounter++
  return `${prefix}-${idCounter}-${Date.now()}`
}

// Color contrast checker
export function meetsContrastRequirements(foreground: string, background: string, level: 'AA' | 'AAA' = 'AA'): boolean {
  // This is a simplified version - in production, use a proper color contrast library
  const minRatio = level === 'AAA' ? 7 : 4.5
  // Implement actual contrast ratio calculation here
  return true // Placeholder
}

// Announce page title changes
export function announcePageChange(title: string) {
  document.title = `${title} - Aegis`
  announceToScreenReader(`Navigated to ${title}`, 'assertive')
}

// High contrast mode detection
export function isHighContrastMode(): boolean {
  return window.matchMedia('(prefers-contrast: high)').matches
}

// Add landmark roles programmatically if missing
export function ensureLandmarks() {
  const main = document.querySelector('main')
  const header = document.querySelector('header')
  const nav = document.querySelector('nav')
  const footer = document.querySelector('footer')

  if (main && !main.getAttribute('role')) {
    main.setAttribute('role', 'main')
    main.id = 'main-content'
  }
  if (header && !header.getAttribute('role')) {
    header.setAttribute('role', 'banner')
  }
  if (nav && !nav.getAttribute('role')) {
    nav.setAttribute('role', 'navigation')
  }
  if (footer && !footer.getAttribute('role')) {
    footer.setAttribute('role', 'contentinfo')
  }
}

