/**
 * Animation Utilities with Reduced Motion Support
 */

import { prefersReducedMotion } from './accessibility'

// Animation configurations
export const animations = {
  // Fade animations
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.3 },
  },
  fadeOut: {
    initial: { opacity: 1 },
    animate: { opacity: 0 },
    transition: { duration: 0.3 },
  },

  // Slide animations
  slideUp: {
    initial: { opacity: 0, y: 10 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.3 },
  },
  slideDown: {
    initial: { opacity: 0, y: -10 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.3 },
  },
  slideLeft: {
    initial: { opacity: 0, x: 10 },
    animate: { opacity: 1, x: 0 },
    transition: { duration: 0.3 },
  },
  slideRight: {
    initial: { opacity: 0, x: -10 },
    animate: { opacity: 1, x: 0 },
    transition: { duration: 0.3 },
  },

  // Scale animations
  scaleIn: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    transition: { duration: 0.2 },
  },
  scaleOut: {
    initial: { opacity: 1, scale: 1 },
    animate: { opacity: 0, scale: 0.95 },
    transition: { duration: 0.2 },
  },

  // Stagger children
  staggerChildren: {
    animate: {
      transition: {
        staggerChildren: 0.05,
      },
    },
  },
}

// Get animation config respecting reduced motion preference
export function getAnimation(animationName: keyof typeof animations) {
  if (prefersReducedMotion()) {
    return {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      transition: { duration: 0.01 },
    }
  }
  return animations[animationName]
}

// Smooth scroll utility
export function smoothScroll(elementId: string, offset: number = 0) {
  const element = document.getElementById(elementId)
  if (!element) return

  const targetPosition = element.getBoundingClientRect().top + window.pageYOffset - offset
  
  if (prefersReducedMotion()) {
    window.scrollTo(0, targetPosition)
  } else {
    window.scrollTo({
      top: targetPosition,
      behavior: 'smooth',
    })
  }
}

// Page transition animations
export const pageTransitions = {
  initial: prefersReducedMotion()
    ? { opacity: 1 }
    : { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: prefersReducedMotion()
    ? { opacity: 1 }
    : { opacity: 0, y: -20 },
  transition: { duration: prefersReducedMotion() ? 0.01 : 0.3 },
}

// Hover animation classes (CSS)
export const hoverClasses = {
  lift: 'transition-transform hover:-translate-y-1 hover:shadow-lg',
  grow: 'transition-transform hover:scale-105',
  glow: 'transition-shadow hover:shadow-primary/50',
  brighten: 'transition-all hover:brightness-110',
}

// Loading animation
export function animateLoadingSkeleton() {
  return prefersReducedMotion()
    ? 'animate-none'
    : 'animate-pulse'
}

// Notification entrance animation
export const notificationAnimation = {
  enter: prefersReducedMotion()
    ? 'animate-none opacity-100'
    : 'animate-slide-in',
  exit: prefersReducedMotion()
    ? 'animate-none opacity-0'
    : 'animate-slide-out',
}

