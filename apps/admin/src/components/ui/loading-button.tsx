/**
 * Loading Button Component
 * Button with built-in loading state and spinner
 */

import { Loader2 } from 'lucide-react';
import React from 'react';

import { Button } from './button';

export interface LoadingButtonProps
  extends React.ComponentProps<typeof Button> {
  loading?: boolean;
  loadingText?: string;
}

export const LoadingButton = React.forwardRef<
  HTMLButtonElement,
  LoadingButtonProps
>(({ children, loading = false, loadingText, disabled, ...props }, ref) => {
  return (
    <Button ref={ref} disabled={disabled || loading} {...props}>
      {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
      {loading && loadingText ? loadingText : children}
    </Button>
  );
});

LoadingButton.displayName = 'LoadingButton';
