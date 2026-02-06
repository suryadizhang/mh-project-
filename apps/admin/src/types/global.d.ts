// Global type declarations for admin app
// Only declare asset modules, not TypeScript source files

declare module '*.json' {
  const value: unknown;
  export default value;
}

declare module '*.css';
declare module '*.svg';
declare module '*.png';
declare module '*.jpg';
declare module '*.jpeg';
