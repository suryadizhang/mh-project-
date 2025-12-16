'use client';

import React, { useRef, useEffect, useState, ReactNode } from 'react';

interface CenteredFlexGridProps {
  children: ReactNode;
  className?: string;
  itemMinWidth: number; // Minimum width of each item in pixels
  gap?: number; // Gap between items in pixels
}

/**
 * A flex grid that centers partial rows (last row with fewer items)
 * Uses ResizeObserver to dynamically calculate and apply centering
 */
export function CenteredFlexGrid({
  children,
  className = '',
  itemMinWidth,
  gap = 16,
}: CenteredFlexGridProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [paddingLeft, setPaddingLeft] = useState(0);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const calculatePadding = () => {
      const containerWidth = container.offsetWidth;
      const itemsPerRow = Math.floor((containerWidth + gap) / (itemMinWidth + gap));
      const childCount = React.Children.count(children);

      if (itemsPerRow <= 0 || childCount <= 0) {
        setPaddingLeft(0);
        return;
      }

      const itemsOnLastRow = childCount % itemsPerRow || itemsPerRow;

      // If last row is full, no padding needed
      if (itemsOnLastRow === itemsPerRow) {
        setPaddingLeft(0);
        return;
      }

      // Calculate actual item width (they may be larger than min)
      const totalGapWidth = (itemsPerRow - 1) * gap;
      const actualItemWidth = (containerWidth - totalGapWidth) / itemsPerRow;

      // Calculate empty space on last row
      const emptySlots = itemsPerRow - itemsOnLastRow;
      const emptyWidth = emptySlots * (actualItemWidth + gap);

      // Center by adding half the empty width as padding
      setPaddingLeft(emptyWidth / 2);
    };

    // Initial calculation
    calculatePadding();

    // Recalculate on resize
    const resizeObserver = new ResizeObserver(() => {
      calculatePadding();
    });

    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
    };
  }, [children, itemMinWidth, gap]);

  // Convert children to array and identify last row items
  const childArray = React.Children.toArray(children);
  const containerWidth = containerRef.current?.offsetWidth || 1000;
  const itemsPerRow = Math.max(1, Math.floor((containerWidth + gap) / (itemMinWidth + gap)));
  const totalItems = childArray.length;
  const itemsOnLastRow = totalItems % itemsPerRow || itemsPerRow;
  const lastRowStartIndex = totalItems - itemsOnLastRow;

  return (
    <div
      ref={containerRef}
      className={className}
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'flex-start',
        gap: `${gap}px`,
        width: '100%',
      }}
    >
      {childArray.map((child, index) => {
        // Add left margin to first item of last row to center it
        const isFirstOfLastRow = index === lastRowStartIndex && itemsOnLastRow < itemsPerRow;

        return (
          <div
            key={index}
            style={{
              flex: `1 1 ${itemMinWidth}px`,
              maxWidth: `${itemMinWidth + 40}px`,
              marginLeft: isFirstOfLastRow ? `${paddingLeft}px` : undefined,
            }}
          >
            {child}
          </div>
        );
      })}
    </div>
  );
}
