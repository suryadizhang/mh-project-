module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  parserOptions: { project: false, ecmaVersion: 2023, sourceType: 'module' },
  plugins: ['@typescript-eslint', 'import', 'unused-imports', 'simple-import-sort'],
  extends: ['next/core-web-vitals', 'plugin:@typescript-eslint/recommended'],
  rules: {
    'no-console': ['error', { allow: ['warn', 'error'] }],
    'import/order': 'off',
    'simple-import-sort/imports': 'error',
    'simple-import-sort/exports': 'error',
    'unused-imports/no-unused-imports': 'error',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }]
  },
  ignorePatterns: ['.next/**', 'out/**', 'node_modules/**']
};
