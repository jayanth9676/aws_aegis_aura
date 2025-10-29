/**
 * Mobile Optimization Utilities
 */

// Detect mobile device
export function isMobileDevice(): boolean {
  if (typeof window === 'undefined') return false
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
}

// Detect touch device
export function isTouchDevice(): boolean {
  if (typeof window === 'undefined') return false
  return 'ontouchstart' in window || navigator.maxTouchPoints > 0
}

// Get viewport size
export function getViewportSize() {
  if (typeof window === 'undefined') return { width: 0, height: 0 }
  return {
    width: window.innerWidth,
    height: window.innerHeight,
  }
}

// Check if mobile viewport
export function isMobileViewport(): boolean {
  const { width } = getViewportSize()
  return width < 768
}

// Check if tablet viewport
export function isTabletViewport(): boolean {
  const { width } = getViewportSize()
  return width >= 768 && width < 1024
}

// Check if desktop viewport
export function isDesktopViewport(): boolean {
  const { width } = getViewportSize()
  return width >= 1024
}

// Prevent body scroll (for modals on mobile)
export function preventBodyScroll() {
  document.body.style.overflow = 'hidden'
  document.body.style.position = 'fixed'
  document.body.style.width = '100%'
}

// Restore body scroll
export function restoreBodyScroll() {
  document.body.style.overflow = ''
  document.body.style.position = ''
  document.body.style.width = ''
}

// Handle safe area insets for iOS
export function getSafeAreaInsets() {
  if (typeof window === 'undefined') return { top: 0, right: 0, bottom: 0, left: 0 }
  
  const style = getComputedStyle(document.documentElement)
  return {
    top: parseInt(style.getPropertyValue('env(safe-area-inset-top)') || '0'),
    right: parseInt(style.getPropertyValue('env(safe-area-inset-right)') || '0'),
    bottom: parseInt(style.getPropertyValue('env(safe-area-inset-bottom)') || '0'),
    left: parseInt(style.getPropertyValue('env(safe-area-inset-left)') || '0'),
  }
}

// Haptic feedback for mobile
export function triggerHapticFeedback(type: 'light' | 'medium' | 'heavy' = 'medium') {
  if (typeof window === 'undefined' || !('vibrate' in navigator)) return
  
  const patterns = {
    light: [10],
    medium: [20],
    heavy: [30],
  }
  
  navigator.vibrate(patterns[type])
}

// Detect network speed
export function getNetworkSpeed(): 'slow' | 'fast' | 'unknown' {
  if (typeof navigator === 'undefined' || !('connection' in navigator)) return 'unknown'
  
  const connection = (navigator as any).connection
  const effectiveType = connection?.effectiveType
  
  if (effectiveType === '4g' || effectiveType === '5g') return 'fast'
  if (effectiveType === '2g' || effectiveType === 'slow-2g') return 'slow'
  
  return 'unknown'
}

// Optimize images for mobile
export function getMobileImageSize(width: number): number {
  const dpr = typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1
  return Math.ceil(width * dpr)
}

// Handle orientation change
export function onOrientationChange(callback: (orientation: 'portrait' | 'landscape') => void) {
  if (typeof window === 'undefined') return () => {}
  
  const handleOrientationChange = () => {
    const orientation = window.innerHeight > window.innerWidth ? 'portrait' : 'landscape'
    callback(orientation)
  }
  
  window.addEventListener('orientationchange', handleOrientationChange)
  window.addEventListener('resize', handleOrientationChange)
  
  return () => {
    window.removeEventListener('orientationchange', handleOrientationChange)
    window.removeEventListener('resize', handleOrientationChange)
  }
}

// Pull to refresh handler
export function enablePullToRefresh(onRefresh: () => Promise<void>) {
  if (typeof window === 'undefined') return () => {}
  
  let startY = 0
  let currentY = 0
  let isRefreshing = false
  
  const handleTouchStart = (e: TouchEvent) => {
    startY = e.touches[0].clientY
  }
  
  const handleTouchMove = (e: TouchEvent) => {
    currentY = e.touches[0].clientY
    
    if (window.scrollY === 0 && currentY > startY && !isRefreshing) {
      e.preventDefault()
    }
  }
  
  const handleTouchEnd = async () => {
    if (window.scrollY === 0 && currentY - startY > 100 && !isRefreshing) {
      isRefreshing = true
      await onRefresh()
      isRefreshing = false
    }
  }
  
  document.addEventListener('touchstart', handleTouchStart, { passive: false })
  document.addEventListener('touchmove', handleTouchMove, { passive: false })
  document.addEventListener('touchend', handleTouchEnd)
  
  return () => {
    document.removeEventListener('touchstart', handleTouchStart)
    document.removeEventListener('touchmove', handleTouchMove)
    document.removeEventListener('touchend', handleTouchEnd)
  }
}

