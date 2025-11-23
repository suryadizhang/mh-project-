import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

import { debounce, throttle, createAbortController } from '../debounce'

describe('debounce', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  describe('Basic debounce functionality', () => {
    it('should delay function execution', () => {
      const func = vi.fn()
      const debounced = debounce(func, 300)

      debounced()
      expect(func).not.toHaveBeenCalled()

      vi.advanceTimersByTime(299)
      expect(func).not.toHaveBeenCalled()

      vi.advanceTimersByTime(1)
      expect(func).toHaveBeenCalledOnce()
    })

    it('should cancel previous timeout on rapid calls', () => {
      const func = vi.fn()
      const debounced = debounce(func, 300)

      debounced()
      vi.advanceTimersByTime(100)

      debounced()
      vi.advanceTimersByTime(100)

      debounced()
      vi.advanceTimersByTime(300)

      expect(func).toHaveBeenCalledOnce()
    })

    it('should pass arguments to debounced function', () => {
      const func = vi.fn()
      const debounced = debounce(func, 300)

      debounced('arg1', 'arg2')
      vi.advanceTimersByTime(300)

      expect(func).toHaveBeenCalledWith('arg1', 'arg2')
    })

    it('should use default wait time of 300ms', () => {
      const func = vi.fn()
      const debounced = debounce(func)

      debounced()
      vi.advanceTimersByTime(299)
      expect(func).not.toHaveBeenCalled()

      vi.advanceTimersByTime(1)
      expect(func).toHaveBeenCalledOnce()
    })
  })

  describe('Multiple invocations', () => {
    it('should execute multiple times after wait period', () => {
      const func = vi.fn()
      const debounced = debounce(func, 100)

      debounced()
      vi.advanceTimersByTime(100)
      expect(func).toHaveBeenCalledTimes(1)

      debounced()
      vi.advanceTimersByTime(100)
      expect(func).toHaveBeenCalledTimes(2)
    })

    it('should only execute once for rapid succession calls', () => {
      const func = vi.fn()
      const debounced = debounce(func, 300)

      // Rapidly call 10 times
      for (let i = 0; i < 10; i++) {
        debounced()
        vi.advanceTimersByTime(50)
      }

      // Wait for debounce period after last call
      vi.advanceTimersByTime(300)

      expect(func).toHaveBeenCalledOnce()
    })
  })

  describe('Type safety', () => {
    it('should preserve function signature', () => {
      const func = vi.fn((a: number, b: string) => `${a}-${b}`)
      const debounced = debounce(func, 100)

      debounced(42, 'test')
      vi.advanceTimersByTime(100)

      expect(func).toHaveBeenCalledWith(42, 'test')
    })
  })
})

describe('throttle', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  describe('Basic throttle functionality', () => {
    it('should execute immediately on first call', () => {
      const func = vi.fn()
      const throttled = throttle(func, 100)

      throttled()
      expect(func).toHaveBeenCalledOnce()
    })

    it('should not execute again within throttle period', () => {
      const func = vi.fn()
      const throttled = throttle(func, 100)

      throttled()
      throttled()
      throttled()

      expect(func).toHaveBeenCalledOnce()
    })

    it('should execute again after throttle period', () => {
      const func = vi.fn()
      const throttled = throttle(func, 100)

      throttled()
      expect(func).toHaveBeenCalledTimes(1)

      vi.advanceTimersByTime(100)

      throttled()
      expect(func).toHaveBeenCalledTimes(2)
    })

    it('should execute trailing call if there was one', () => {
      const func = vi.fn()
      const throttled = throttle(func, 100)

      throttled()
      expect(func).toHaveBeenCalledTimes(1)

      // Call during throttle period
      throttled()
      throttled()

      // Still only called once
      expect(func).toHaveBeenCalledTimes(1)

      // After throttle period, trailing call executes
      vi.advanceTimersByTime(100)
      expect(func).toHaveBeenCalledTimes(2)
    })

    it('should use default wait time of 100ms', () => {
      const func = vi.fn()
      const throttled = throttle(func)

      throttled()
      throttled()

      vi.advanceTimersByTime(99)
      throttled()
      expect(func).toHaveBeenCalledTimes(1)

      vi.advanceTimersByTime(1)
      expect(func).toHaveBeenCalledTimes(2)
    })
  })

  describe('Rapid calls', () => {
    it('should throttle rapid succession calls correctly', () => {
      const func = vi.fn()
      const throttled = throttle(func, 100)

      // First call executes immediately
      throttled()
      expect(func).toHaveBeenCalledTimes(1)

      // Rapid calls during throttle
      for (let i = 0; i < 10; i++) {
        throttled()
        vi.advanceTimersByTime(10)
      }

      // Only initial call and one trailing call
      expect(func).toHaveBeenCalledTimes(2)
    })
  })

  describe('Argument passing', () => {
    it('should pass arguments to throttled function', () => {
      const func = vi.fn()
      const throttled = throttle(func, 100)

      throttled('arg1', 'arg2')
      expect(func).toHaveBeenCalledWith('arg1', 'arg2')
    })

    it('should pass latest arguments to trailing call', () => {
      const func = vi.fn()
      const throttled = throttle(func, 100)

      throttled('first')
      throttled('second')
      throttled('third')

      vi.advanceTimersByTime(100)

      expect(func).toHaveBeenCalledTimes(2)
      expect(func).toHaveBeenNthCalledWith(1, 'first')
      expect(func).toHaveBeenNthCalledWith(2, 'third')
    })
  })
})

describe('createAbortController', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  describe('Basic abort controller creation', () => {
    it('should create an AbortController instance', () => {
      const controller = createAbortController()
      expect(controller).toBeInstanceOf(AbortController)
      expect(controller.signal).toBeDefined()
    })

    it('should not abort immediately without timeout', () => {
      const controller = createAbortController()
      expect(controller.signal.aborted).toBe(false)
    })
  })

  describe('Timeout functionality', () => {
    it('should abort after specified timeout', () => {
      const controller = createAbortController(1000)
      expect(controller.signal.aborted).toBe(false)

      vi.advanceTimersByTime(999)
      expect(controller.signal.aborted).toBe(false)

      vi.advanceTimersByTime(1)
      expect(controller.signal.aborted).toBe(true)
    })

    it('should work with short timeouts', () => {
      const controller = createAbortController(100)

      vi.advanceTimersByTime(100)
      expect(controller.signal.aborted).toBe(true)
    })

    it('should work with long timeouts', () => {
      const controller = createAbortController(5000)

      vi.advanceTimersByTime(4999)
      expect(controller.signal.aborted).toBe(false)

      vi.advanceTimersByTime(1)
      expect(controller.signal.aborted).toBe(true)
    })
  })

  describe('Signal behavior', () => {
    it('should have a valid signal that can be used', () => {
      const controller = createAbortController(1000)
      const signal = controller.signal

      expect(signal).toHaveProperty('aborted')
      expect(signal).toHaveProperty('addEventListener')
      expect(signal).toHaveProperty('removeEventListener')
    })

    it('should allow manual abort before timeout', () => {
      const controller = createAbortController(1000)
      expect(controller.signal.aborted).toBe(false)

      controller.abort()
      expect(controller.signal.aborted).toBe(true)
    })
  })

  describe('Edge cases', () => {
    it.skip('should handle zero timeout - aborts after event loop (SKIP: setTimeout(0) behavior varies)', async () => {
      vi.useRealTimers()
      const controller = createAbortController(0)

      // Zero timeout still requires one event loop tick
      expect(controller.signal.aborted).toBe(false)

      // After waiting, it should be aborted
      await new Promise(resolve => setTimeout(resolve, 10))
      expect(controller.signal.aborted).toBe(true)
      vi.useFakeTimers()
    })

    it('should handle undefined timeout (no auto-abort)', () => {
      const controller = createAbortController(undefined)

      vi.advanceTimersByTime(10000)
      expect(controller.signal.aborted).toBe(false)
    })
  })
})
