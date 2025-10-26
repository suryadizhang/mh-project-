import { describe, it, expect } from 'vitest'

import { cn } from '../utils'

describe('cn utility function', () => {
  describe('Basic class merging', () => {
    it('should merge simple class names', () => {
      const result = cn('text-red-500', 'bg-blue-500')
      expect(result).toContain('text-red-500')
      expect(result).toContain('bg-blue-500')
    })

    it('should handle single class name', () => {
      const result = cn('text-lg')
      expect(result).toBe('text-lg')
    })

    it('should handle empty input', () => {
      const result = cn()
      expect(result).toBe('')
    })

    it('should handle undefined values', () => {
      const result = cn('text-lg', undefined, 'bg-blue-500')
      expect(result).toContain('text-lg')
      expect(result).toContain('bg-blue-500')
    })

    it('should handle null values', () => {
      const result = cn('text-lg', null, 'bg-blue-500')
      expect(result).toContain('text-lg')
      expect(result).toContain('bg-blue-500')
    })
  })

  describe('Conditional class names', () => {
    it('should handle conditional classes with boolean', () => {
      const isActive = true
      const result = cn('base-class', isActive && 'active-class')
      expect(result).toContain('base-class')
      expect(result).toContain('active-class')
    })

    it('should exclude false conditional classes', () => {
      const isActive = false
      const result = cn('base-class', isActive && 'active-class')
      expect(result).toBe('base-class')
      expect(result).not.toContain('active-class')
    })

    it('should handle multiple conditional classes', () => {
      const isActive = true
      const isDisabled = false
      const result = cn(
        'base-class',
        isActive && 'active-class',
        isDisabled && 'disabled-class'
      )
      expect(result).toContain('base-class')
      expect(result).toContain('active-class')
      expect(result).not.toContain('disabled-class')
    })
  })

  describe('Tailwind class merging', () => {
    it('should merge conflicting Tailwind classes (last one wins)', () => {
      const result = cn('text-red-500', 'text-blue-500')
      expect(result).toBe('text-blue-500')
      expect(result).not.toContain('text-red-500')
    })

    it('should handle padding conflicts', () => {
      const result = cn('p-4', 'p-8')
      expect(result).toBe('p-8')
    })

    it('should handle margin conflicts', () => {
      const result = cn('m-2', 'm-6')
      expect(result).toBe('m-6')
    })

    it('should keep non-conflicting classes', () => {
      const result = cn('text-red-500 bg-blue-500', 'text-green-500')
      expect(result).toContain('bg-blue-500')
      expect(result).toContain('text-green-500')
      expect(result).not.toContain('text-red-500')
    })
  })

  describe('Array and object inputs', () => {
    it('should handle array of classes', () => {
      const result = cn(['text-lg', 'font-bold'])
      expect(result).toContain('text-lg')
      expect(result).toContain('font-bold')
    })

    it('should handle object with boolean values', () => {
      const result = cn({
        'text-lg': true,
        'font-bold': true,
        'italic': false
      })
      expect(result).toContain('text-lg')
      expect(result).toContain('font-bold')
      expect(result).not.toContain('italic')
    })

    it('should handle mixed array and string inputs', () => {
      const result = cn('base-class', ['text-lg', 'font-bold'], 'extra-class')
      expect(result).toContain('base-class')
      expect(result).toContain('text-lg')
      expect(result).toContain('font-bold')
      expect(result).toContain('extra-class')
    })
  })

  describe('Real-world usage patterns', () => {
    it('should handle button variant pattern', () => {
      const variant = 'primary'
      const size = 'lg'
      const result = cn(
        'button',
        variant === 'primary' && 'bg-blue-500 text-white',
        size === 'lg' && 'px-6 py-3'
      )
      expect(result).toContain('button')
      expect(result).toContain('bg-blue-500')
      expect(result).toContain('text-white')
      expect(result).toContain('px-6')
      expect(result).toContain('py-3')
    })

    it('should handle disabled state pattern', () => {
      const isDisabled = true
      const result = cn(
        'button bg-blue-500',
        isDisabled && 'opacity-50 cursor-not-allowed'
      )
      expect(result).toContain('button')
      expect(result).toContain('bg-blue-500')
      expect(result).toContain('opacity-50')
      expect(result).toContain('cursor-not-allowed')
    })

    it('should handle loading state pattern', () => {
      const isLoading = true
      const result = cn(
        'button',
        isLoading ? 'bg-gray-400 cursor-wait' : 'bg-blue-500 hover:bg-blue-600'
      )
      expect(result).toContain('button')
      expect(result).toContain('bg-gray-400')
      expect(result).toContain('cursor-wait')
      expect(result).not.toContain('bg-blue-500')
      expect(result).not.toContain('hover:bg-blue-600')
    })
  })

  describe('Edge cases', () => {
    it('should handle very long class strings', () => {
      const longClasses = Array(50).fill('text-sm').join(' ')
      const result = cn(longClasses)
      expect(result).toBe('text-sm')
    })

    it('should handle special characters in class names', () => {
      const result = cn('hover:bg-blue-500', 'focus:ring-2')
      expect(result).toContain('hover:bg-blue-500')
      expect(result).toContain('focus:ring-2')
    })

    it('should handle numeric class values', () => {
      const result = cn('w-1/2', 'h-full')
      expect(result).toContain('w-1/2')
      expect(result).toContain('h-full')
    })

    it('should handle arbitrary values', () => {
      const result = cn('bg-[#1da1f2]', 'text-[14px]')
      expect(result).toContain('bg-[#1da1f2]')
      expect(result).toContain('text-[14px]')
    })
  })
})
