import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

import { FlatCompat } from '@eslint/eslintrc';
import typescriptParser from '@typescript-eslint/parser';
import typescriptPlugin from '@typescript-eslint/eslint-plugin';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

/**
 * Root ESLint configuration for My Hibachi monorepo.
 * This delegates linting to app-specific configs for frontend projects
 * and provides basic settings for root-level files.
 */
const eslintConfig = [
  // Global ignores
  {
    ignores: [
      // Build artifacts
      '**/node_modules/**',
      '**/.next/**',
      '**/out/**',
      '**/dist/**',
      '**/build/**',
      '**/.cache/**',
      '**/coverage/**',
      '**/.turbo/**',
      '**/public/**',

      // Config files that don't need linting
      '**/*.config.js',
      '**/*.config.mjs',
      '**/*.config.ts',
      '**/next-env.d.ts',

      // Backend Python files
      'apps/backend/**',

      // Database and scripts
      'database/**',
      'scripts/**',

      // Documentation
      'docs/**',

      // Archive files
      'archives/**',
    ],
  },

  // TypeScript/JavaScript files in apps/customer
  {
    files: ['apps/customer/**/*.{js,jsx,ts,tsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parser: typescriptParser,
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    plugins: {
      '@typescript-eslint': typescriptPlugin,
    },
    rules: {
      // Basic rules - actual linting is done by app-specific config
      'no-trailing-spaces': 'error',
      'eol-last': ['error', 'always'],
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
    },
  },

  // TypeScript/JavaScript files in apps/admin
  {
    files: ['apps/admin/**/*.{js,jsx,ts,tsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parser: typescriptParser,
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    plugins: {
      '@typescript-eslint': typescriptPlugin,
    },
    rules: {
      'no-trailing-spaces': 'error',
      'eol-last': ['error', 'always'],
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
    },
  },

  // Root-level JavaScript/TypeScript files
  {
    files: ['*.{js,jsx,ts,tsx}'],
    ignores: ['apps/**', 'libs/**'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parser: typescriptParser,
    },
    plugins: {
      '@typescript-eslint': typescriptPlugin,
    },
    rules: {
      'no-trailing-spaces': 'error',
      'eol-last': ['error', 'always'],
    },
  },

  // Library files
  {
    files: ['libs/**/*.{js,jsx,ts,tsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parser: typescriptParser,
    },
    plugins: {
      '@typescript-eslint': typescriptPlugin,
    },
    rules: {
      'no-trailing-spaces': 'error',
      'eol-last': ['error', 'always'],
    },
  },
];

export default eslintConfig;
