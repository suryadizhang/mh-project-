import { dirname } from 'path'
import { fileURLToPath } from 'url'

import { FlatCompat } from '@eslint/eslintrc'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const compat = new FlatCompat({
  baseDirectory: __dirname
})

const eslintConfig = [
  {
    ignores: [
      '.next/**',
      'out/**',
      'node_modules/**',
      'dist/**',
      'build/**',
      '.cache/**',
      'public/**',
      '*.config.js',
      '*.config.mjs',
      '*.config.ts',
      'coverage/**',
      '.turbo/**',
      'next-env.d.ts' // Next.js auto-generated type definitions
    ]
  },
  ...compat.extends('next/core-web-vitals', 'next/typescript'),
  {
    rules: {
      // Formatting and whitespace rules
      'no-trailing-spaces': 'error',
      'eol-last': ['error', 'always'],
      'no-multiple-empty-lines': ['error', { max: 2, maxEOF: 1 }],

      // Import organization
      'import/order': [
        'error',
        {
          groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index'],
          'newlines-between': 'always'
        }
      ],

      // Unused code detection
      'no-unused-vars': 'off', // Let TypeScript handle this
      '@typescript-eslint/no-unused-vars': [
        'warn', // Changed to warn to avoid blocking builds
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_'
        }
      ],

      // Import/export consistency
      'no-duplicate-imports': 'error',

      // Disable rules that may cause issues
      '@typescript-eslint/no-explicit-any': 'warn',
      'react-hooks/exhaustive-deps': 'warn',
      'no-console': 'off'
    }
  }
]

export default eslintConfig
