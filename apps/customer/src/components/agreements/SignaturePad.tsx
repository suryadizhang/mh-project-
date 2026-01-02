'use client';

/**
 * SignaturePad Component
 * ======================
 *
 * Canvas-based signature capture with:
 * - Touch and mouse support
 * - Clear functionality
 * - PNG export for storage
 * - Mobile-responsive design
 *
 * Per LEGAL_PROTECTION_IMPLEMENTATION.md:
 * - D1) Hybrid SignaturePad + timestamp + email PDF
 */

import { useRef, useEffect, useState, useCallback } from 'react';

interface SignaturePadProps {
  /** Callback when signature changes (base64 PNG or null if cleared) */
  onSignatureChange: (signature: string | null) => void;
  /** Optional width (default: 100%) */
  width?: number | string;
  /** Optional height (default: 200px) */
  height?: number;
  /** Disable interaction */
  disabled?: boolean;
  /** Pen color (default: #1f2937) */
  penColor?: string;
  /** Background color (default: #f9fafb) */
  backgroundColor?: string;
}

export default function SignaturePad({
  onSignatureChange,
  width = '100%',
  height = 200,
  disabled = false,
  penColor = '#1f2937',
  backgroundColor = '#f9fafb',
}: SignaturePadProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasSignature, setHasSignature] = useState(false);
  const lastPointRef = useRef<{ x: number; y: number } | null>(null);

  // Initialize canvas with proper dimensions
  const initCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    // Get the actual display size
    const rect = container.getBoundingClientRect();
    const displayWidth = rect.width;
    const displayHeight = height;

    // Set the canvas internal resolution (2x for retina)
    const dpr = window.devicePixelRatio || 1;
    canvas.width = displayWidth * dpr;
    canvas.height = displayHeight * dpr;

    // Scale the context to match
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.scale(dpr, dpr);
      ctx.fillStyle = backgroundColor;
      ctx.fillRect(0, 0, displayWidth, displayHeight);
      ctx.strokeStyle = penColor;
      ctx.lineWidth = 2;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
    }
  }, [height, backgroundColor, penColor]);

  // Initialize on mount and resize
  useEffect(() => {
    initCanvas();

    const handleResize = () => {
      // Only reinit if container size changed
      initCanvas();
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [initCanvas]);

  // Get coordinates from event (mouse or touch)
  const getCoordinates = useCallback(
    (
      e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>,
    ): { x: number; y: number } | null => {
      const canvas = canvasRef.current;
      if (!canvas) return null;

      const rect = canvas.getBoundingClientRect();
      let clientX: number;
      let clientY: number;

      if ('touches' in e) {
        if (e.touches.length === 0) return null;
        clientX = e.touches[0].clientX;
        clientY = e.touches[0].clientY;
      } else {
        clientX = e.clientX;
        clientY = e.clientY;
      }

      return {
        x: clientX - rect.left,
        y: clientY - rect.top,
      };
    },
    [],
  );

  // Start drawing
  const startDrawing = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
      if (disabled) return;
      e.preventDefault();

      const coords = getCoordinates(e);
      if (!coords) return;

      setIsDrawing(true);
      lastPointRef.current = coords;
    },
    [disabled, getCoordinates],
  );

  // Draw while moving
  const draw = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
      if (!isDrawing || disabled) return;
      e.preventDefault();

      const coords = getCoordinates(e);
      if (!coords || !lastPointRef.current) return;

      const canvas = canvasRef.current;
      const ctx = canvas?.getContext('2d');
      if (!ctx) return;

      ctx.beginPath();
      ctx.moveTo(lastPointRef.current.x, lastPointRef.current.y);
      ctx.lineTo(coords.x, coords.y);
      ctx.stroke();

      lastPointRef.current = coords;
      setHasSignature(true);
    },
    [isDrawing, disabled, getCoordinates],
  );

  // Stop drawing and export signature
  const stopDrawing = useCallback(() => {
    if (!isDrawing) return;

    setIsDrawing(false);
    lastPointRef.current = null;

    // Export signature as base64 PNG
    const canvas = canvasRef.current;
    if (canvas && hasSignature) {
      const dataUrl = canvas.toDataURL('image/png');
      onSignatureChange(dataUrl);
    }
  }, [isDrawing, hasSignature, onSignatureChange]);

  // Clear signature
  const clearSignature = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!ctx || !canvas) return;

    const container = containerRef.current;
    if (!container) return;

    const rect = container.getBoundingClientRect();
    ctx.fillStyle = backgroundColor;
    ctx.fillRect(0, 0, rect.width, height);

    setHasSignature(false);
    onSignatureChange(null);
  }, [backgroundColor, height, onSignatureChange]);

  return (
    <div className="space-y-2">
      <div
        ref={containerRef}
        className="relative overflow-hidden rounded-lg border-2 border-dashed border-gray-300"
        style={{ width, height }}
      >
        <canvas
          ref={canvasRef}
          className={`touch-none ${
            disabled ? 'cursor-not-allowed opacity-50' : 'cursor-crosshair'
          }`}
          style={{
            width: '100%',
            height: '100%',
            display: 'block',
          }}
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          onTouchStart={startDrawing}
          onTouchMove={draw}
          onTouchEnd={stopDrawing}
          onTouchCancel={stopDrawing}
        />

        {/* Signature line */}
        <div
          className="pointer-events-none absolute right-8 bottom-8 left-8 border-b-2 border-gray-300"
          aria-hidden="true"
        />

        {/* X mark */}
        <div className="pointer-events-none absolute bottom-6 left-6 text-lg text-gray-400">✗</div>

        {/* Placeholder text */}
        {!hasSignature && (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <p className="text-sm text-gray-400">Sign here</p>
          </div>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={clearSignature}
          disabled={disabled || !hasSignature}
          className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
            disabled || !hasSignature
              ? 'cursor-not-allowed text-gray-400'
              : 'text-gray-600 hover:bg-gray-100 hover:text-gray-800'
          }`}
        >
          Clear
        </button>
      </div>

      {/* Accessibility note */}
      <p className="text-xs text-gray-400">Use your mouse or finger to draw your signature above</p>
    </div>
  );
}
