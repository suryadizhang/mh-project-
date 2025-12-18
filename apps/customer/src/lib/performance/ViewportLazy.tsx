'use client';

/**
 * Viewport-Aware Lazy Loading Components
 *
 * These components only render their children when they enter the viewport,
 * providing maximum performance by deferring component hydration.
 */

import React, { type ReactNode, Suspense } from 'react';
import {
  useIntersectionObserver,
  INTERSECTION_PRESETS,
  type UseIntersectionObserverOptions,
} from './useIntersectionObserver';
import { GenericSkeleton, SectionSkeleton, FormSkeleton } from './lazyComponents';

interface ViewportLazyProps {
  /** The content to render when visible */
  children: ReactNode;
  /** Fallback to show while loading/before visible */
  fallback?: ReactNode;
  /** Intersection observer options */
  options?: UseIntersectionObserverOptions;
  /** Additional className for the wrapper */
  className?: string;
  /** Minimum height to prevent layout shift */
  minHeight?: number | string;
  /** ID for testing/debugging */
  id?: string;
}

/**
 * Generic viewport-aware lazy loader
 *
 * @example
 * ```tsx
 * <ViewportLazy minHeight={400} fallback={<SectionSkeleton />}>
 *   <HeavyComponent />
 * </ViewportLazy>
 * ```
 */
export function ViewportLazy({
  children,
  fallback,
  options = INTERSECTION_PRESETS.preload,
  className = '',
  minHeight,
  id,
}: ViewportLazyProps): React.ReactElement {
  const { ref, hasBeenVisible } = useIntersectionObserver(options);

  const style: React.CSSProperties = minHeight
    ? { minHeight: typeof minHeight === 'number' ? `${minHeight}px` : minHeight }
    : {};

  return (
    <div
      ref={ref as React.RefObject<HTMLDivElement>}
      className={className}
      style={style}
      data-viewport-lazy={id}
    >
      {hasBeenVisible ? (
        <Suspense fallback={fallback || <GenericSkeleton height={minHeight || 200} />}>
          {children}
        </Suspense>
      ) : (
        fallback || <GenericSkeleton height={minHeight || 200} />
      )}
    </div>
  );
}

/**
 * Presets for common section types
 */

/** For hero sections and above-the-fold content - immediate load */
export function ViewportLazyHero({
  children,
  ...props
}: Omit<ViewportLazyProps, 'options'>): React.ReactElement {
  return (
    <ViewportLazy {...props} options={INTERSECTION_PRESETS.immediate}>
      {children}
    </ViewportLazy>
  );
}

/** For below-fold sections - preload 200px before visible */
export function ViewportLazySection({
  children,
  fallback,
  ...props
}: Omit<ViewportLazyProps, 'options' | 'fallback'> & { fallback?: ReactNode }): React.ReactElement {
  return (
    <ViewportLazy
      {...props}
      options={INTERSECTION_PRESETS.aggressivePreload}
      fallback={fallback || <SectionSkeleton />}
      minHeight={props.minHeight || 300}
    >
      {children}
    </ViewportLazy>
  );
}

/** For forms - preload 100px before visible */
export function ViewportLazyForm({
  children,
  ...props
}: Omit<ViewportLazyProps, 'options' | 'fallback'>): React.ReactElement {
  return (
    <ViewportLazy
      {...props}
      options={INTERSECTION_PRESETS.preload}
      fallback={<FormSkeleton />}
      minHeight={props.minHeight || 400}
    >
      {children}
    </ViewportLazy>
  );
}

/** For images and media - aggressive preload */
export function ViewportLazyMedia({
  children,
  ...props
}: Omit<ViewportLazyProps, 'options'>): React.ReactElement {
  return (
    <ViewportLazy {...props} options={INTERSECTION_PRESETS.aggressivePreload}>
      {children}
    </ViewportLazy>
  );
}

/**
 * Hook to check if we're in a slow connection
 * Returns true if connection is slow (2g, slow-2g) or saveData is enabled
 */
export function useSlowConnection(): boolean {
  if (typeof window === 'undefined') return false;

  const nav = navigator as Navigator & {
    connection?: {
      effectiveType?: string;
      saveData?: boolean;
    };
  };

  const connection = nav.connection;
  if (!connection) return false;

  const isSlowConnection = ['slow-2g', '2g'].includes(connection.effectiveType || '');
  const saveData = connection.saveData === true;

  return isSlowConnection || saveData;
}

/**
 * Connection-aware lazy loader
 * On slow connections, uses more aggressive skeleton and doesn't preload
 */
export function ConnectionAwareLazy({
  children,
  fallback,
  className,
  minHeight,
  id,
}: ViewportLazyProps): React.ReactElement {
  const isSlowConnection = useSlowConnection();

  const options = isSlowConnection
    ? INTERSECTION_PRESETS.halfVisible // Wait until 50% visible on slow connections
    : INTERSECTION_PRESETS.aggressivePreload; // Preload 200px on fast connections

  return (
    <ViewportLazy
      options={options}
      fallback={fallback}
      className={className}
      minHeight={minHeight}
      id={id}
    >
      {children}
    </ViewportLazy>
  );
}
