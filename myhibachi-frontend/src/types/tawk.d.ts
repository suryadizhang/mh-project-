// Type definitions for Tawk.to
declare global {
  interface Window {
    Tawk_API: {
      onLoad?: () => void;
      setAttributes?: (attrs: Record<string, string>, callback?: (error?: unknown) => void) => void;
      maximize?: () => void;
    };
    Tawk_LoadStart?: Date;
  }
}

export {};
