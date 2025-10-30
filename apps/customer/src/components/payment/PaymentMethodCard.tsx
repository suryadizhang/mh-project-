import { CheckCircle2 } from 'lucide-react';

interface PaymentMethodCardProps {
  method: {
    id: string;
    name: string;
    icon: string;
    color: string;
    totalAmount: number;
    processingFee: number;
    isFree: boolean;
    isInstant: boolean;
    confirmationTime?: string;
    savingsVsStripe?: number;
  };
  selected: boolean;
  onSelect: () => void;
}

/**
 * PaymentMethodCard Component
 * 
 * Displays a single payment method option with:
 * - Icon and name
 * - Fee information (FREE or +X%)
 * - Confirmation time
 * - Total amount
 * - Best option badge
 */
export function PaymentMethodCard({ method, selected, onSelect }: PaymentMethodCardProps) {
  // Color mapping for border and background
  const colorClasses = {
    purple: {
      border: 'border-purple-500',
      bg: 'bg-purple-50',
      icon: 'bg-purple-600',
      hover: 'hover:border-purple-300',
    },
    blue: {
      border: 'border-blue-500',
      bg: 'bg-blue-50',
      icon: 'bg-blue-600',
      hover: 'hover:border-blue-300',
    },
    green: {
      border: 'border-green-500',
      bg: 'bg-green-50',
      icon: 'bg-green-600',
      hover: 'hover:border-green-300',
    },
    orange: {
      border: 'border-orange-500',
      bg: 'bg-orange-50',
      icon: 'bg-orange-600',
      hover: 'hover:border-orange-300',
    },
  };

  const colors = colorClasses[method.color as keyof typeof colorClasses] || colorClasses.blue;

  return (
    <button
      onClick={onSelect}
      className={`
        relative w-full rounded-2xl border-2 p-6 transition-all duration-200
        ${selected 
          ? `${colors.border} ${colors.bg} scale-105 shadow-xl` 
          : `border-gray-300 ${colors.hover} hover:scale-102 hover:shadow-lg`
        }
      `}
    >
      {/* Selected Checkmark */}
      {selected && (
        <div className="absolute top-3 right-3">
          <CheckCircle2 className="h-6 w-6 text-green-600" />
        </div>
      )}

      {/* Best Badge */}
      {method.isFree && method.isInstant && (
        <div className="absolute top-3 left-3">
          <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-yellow-400 to-yellow-500 px-3 py-1 text-xs font-bold text-yellow-900 shadow-md">
            ⭐ BEST
          </span>
        </div>
      )}

      {/* Icon */}
      <div className={`mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full ${colors.icon} text-white shadow-lg`}>
        <span className="text-2xl font-bold">{method.icon}</span>
      </div>
      
      {/* Method Name */}
      <h3 className="mb-3 text-xl font-bold text-gray-900">{method.name}</h3>
      
      {/* Fee Badge */}
      {method.isFree ? (
        <div className="mb-3 flex flex-col items-center gap-1">
          <span className="inline-block rounded-full bg-green-100 px-4 py-1.5 text-sm font-bold text-green-800">
            FREE ✨
          </span>
          {method.savingsVsStripe && method.savingsVsStripe > 0 && (
            <span className="text-xs text-green-700">
              Save ${method.savingsVsStripe.toFixed(2)}
            </span>
          )}
        </div>
      ) : (
        <div className="mb-3">
          <span className="text-sm font-medium text-orange-600">
            +${method.processingFee.toFixed(2)} fee
          </span>
          <p className="text-xs text-gray-500">
            ({((method.processingFee / (method.totalAmount - method.processingFee)) * 100).toFixed(1)}%)
          </p>
        </div>
      )}
      
      {/* Confirmation Time */}
      <div className="mb-4 flex items-center justify-center gap-2 text-sm text-gray-600">
        {method.isInstant ? (
          <>
            <span className="text-lg">⚡</span>
            <span className="font-medium">Instant</span>
          </>
        ) : (
          <>
            <span className="text-lg">⏱️</span>
            <span>{method.confirmationTime || '1-2 hours'}</span>
          </>
        )}
      </div>
      
      {/* Total Amount */}
      <div className="mt-4 border-t border-gray-200 pt-4">
        <p className="mb-1 text-xs font-medium text-gray-500 uppercase tracking-wide">
          Total Amount
        </p>
        <p className="text-3xl font-bold text-gray-900">
          ${method.totalAmount.toFixed(2)}
        </p>
      </div>

      {/* Hover Effect Indicator */}
      {!selected && (
        <div className="mt-4 text-xs text-gray-400">
          Click to select
        </div>
      )}
    </button>
  );
}
