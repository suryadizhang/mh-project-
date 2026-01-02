'use client';

import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Eraser, Check, AlertCircle } from 'lucide-react';

interface SignaturePadProps {
  /** Called when signature is captured (base64 PNG) */
  onSignatureCapture: (signatureBase64: string | null) => void;
  /** Callback when signature validity changes */
  onValidityChange?: (isValid: boolean) => void;
  /** Width of the signature pad canvas */
  width?: number;
  /** Height of the signature pad canvas */
  height?: number;
  /** Line color for drawing */
  lineColor?: string;
  /** Line width for drawing */
  lineWidth?: number;
  /** Background color of canvas */
  backgroundColor?: string;
  /** Whether the pad is disabled */
  disabled?: boolean;
  /** Custom class name for the container */
  className?: string;
}

/**
 * SignaturePad Component
 *
 * Canvas-based digital signature capture component for legal agreements.
 * Returns signature as base64 PNG for API submission.
 *
 * Used in: BookingAgreementModal.tsx
 * Backend API: POST /api/v1/agreements/sign (signature_image_base64 field)
 *
 * @example
 * <SignaturePad
 *   onSignatureCapture={(base64) => setSignature(base64)}
 *   onValidityChange={(valid) => setHasSignature(valid)}
 * />
 */
export default function SignaturePad({
  onSignatureCapture,
  onValidityChange,
  width = 400,
  height = 150,
  lineColor = '#000000',
  lineWidth = 2,
  backgroundColor = '#ffffff',
  disabled = false,
  className = '',
}: SignaturePadProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasSignature, setHasSignature] = useState(false);
  const [ctx, setCtx] = useState<CanvasRenderingContext2D | null>(null);

  // Initialize canvas context
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const context = canvas.getContext('2d');
    if (!context) return;

    // Set up canvas context
    context.strokeStyle = lineColor;
    context.lineWidth = lineWidth;
    context.lineCap = 'round';
    context.lineJoin = 'round';

    // Fill background
    context.fillStyle = backgroundColor;
    context.fillRect(0, 0, width, height);

    setCtx(context);
  }, [lineColor, lineWidth, backgroundColor, width, height]);

  // Get position relative to canvas (supports both mouse and touch)
  const getPosition = useCallback(
    (event: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
      const canvas = canvasRef.current;
      if (!canvas) return { x: 0, y: 0 };

      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;

      if ('touches' in event) {
        // Touch event
        const touch = event.touches[0] || event.changedTouches[0];
        return {
          x: (touch.clientX - rect.left) * scaleX,
          y: (touch.clientY - rect.top) * scaleY,
        };
      } else {
        // Mouse event
        return {
          x: (event.clientX - rect.left) * scaleX,
          y: (event.clientY - rect.top) * scaleY,
        };
      }
    },
    [],
  );

  // Start drawing
  const startDrawing = useCallback(
    (event: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
      if (disabled || !ctx) return;

      event.preventDefault();
      const { x, y } = getPosition(event);

      ctx.beginPath();
      ctx.moveTo(x, y);
      setIsDrawing(true);
    },
    [ctx, disabled, getPosition],
  );

  // Continue drawing
  const draw = useCallback(
    (event: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
      if (!isDrawing || disabled || !ctx) return;

      event.preventDefault();
      const { x, y } = getPosition(event);

      ctx.lineTo(x, y);
      ctx.stroke();
    },
    [ctx, isDrawing, disabled, getPosition],
  );

  // Stop drawing and capture signature
  const stopDrawing = useCallback(() => {
    if (!isDrawing || !ctx) return;

    ctx.closePath();
    setIsDrawing(false);

    // Check if canvas has any content (signature)
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Get image data and check if it's empty
    const imageData = ctx.getImageData(0, 0, width, height);
    const hasContent = imageData.data.some((pixel, index) => {
      // Check non-alpha channels for non-white pixels (assuming white bg)
      if (index % 4 === 3) return false; // Skip alpha
      return pixel !== 255;
    });

    setHasSignature(hasContent);
    onValidityChange?.(hasContent);

    if (hasContent) {
      // Export as base64 PNG
      const base64 = canvas.toDataURL('image/png');
      onSignatureCapture(base64);
    } else {
      onSignatureCapture(null);
    }
  }, [ctx, isDrawing, width, height, onSignatureCapture, onValidityChange]);

  // Clear signature
  const clearSignature = useCallback(() => {
    if (!ctx || !canvasRef.current) return;

    // Clear and refill with background
    ctx.fillStyle = backgroundColor;
    ctx.fillRect(0, 0, width, height);

    setHasSignature(false);
    onValidityChange?.(false);
    onSignatureCapture(null);
  }, [ctx, width, height, backgroundColor, onSignatureCapture, onValidityChange]);

  // Handle mouse leaving canvas
  const handleMouseLeave = useCallback(() => {
    if (isDrawing) {
      stopDrawing();
    }
  }, [isDrawing, stopDrawing]);

  return (
    <div className={`signature-pad-container ${className}`}>
      {/* Label */}
      <div className="mb-2 flex items-center justify-between">
        <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
          <span className="text-red-500">*</span>
          Digital Signature
        </label>
        {hasSignature && (
          <span className="flex items-center gap-1 text-xs text-green-600">
            <Check className="h-3 w-3" />
            Signature captured
          </span>
        )}
      </div>

      {/* Canvas Container */}
      <div
        className={`relative overflow-hidden rounded-lg border-2 ${
          disabled
            ? 'cursor-not-allowed border-gray-200 bg-gray-100'
            : hasSignature
              ? 'border-green-400 bg-white'
              : 'border-gray-300 bg-white hover:border-red-400'
        } transition-colors duration-200`}
      >
        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          className={`w-full touch-none ${disabled ? 'cursor-not-allowed opacity-50' : 'cursor-crosshair'}`}
          style={{ maxWidth: '100%', height: 'auto' }}
          // Mouse events
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={handleMouseLeave}
          // Touch events for mobile
          onTouchStart={startDrawing}
          onTouchMove={draw}
          onTouchEnd={stopDrawing}
        />

        {/* Placeholder text when empty */}
        {!hasSignature && !isDrawing && (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <span className="text-sm text-gray-400">Sign here with your mouse or finger</span>
          </div>
        )}

        {/* Clear button */}
        {hasSignature && !disabled && (
          <button
            type="button"
            onClick={clearSignature}
            className="absolute top-2 right-2 rounded-md border border-gray-200 bg-white/90 p-1.5 text-gray-500 shadow-sm transition-colors hover:bg-red-50 hover:text-red-600"
            title="Clear signature"
          >
            <Eraser className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Helper text */}
      {!hasSignature && (
        <p className="mt-2 flex items-start gap-1 text-xs text-gray-500">
          <AlertCircle className="mt-0.5 h-3 w-3 flex-shrink-0" />
          <span>
            Draw your signature above to acknowledge the agreement. Your signature is legally
            binding.
          </span>
        </p>
      )}
    </div>
  );
}
