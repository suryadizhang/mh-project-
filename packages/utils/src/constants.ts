export const constants = {
  // API URLs
  API_BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  AI_API_URL: process.env.NEXT_PUBLIC_AI_API_URL || 'http://localhost:8002',
  
  // App URLs
  CUSTOMER_URL: process.env.NEXT_PUBLIC_CUSTOMER_URL || 'http://localhost:3000',
  ADMIN_URL: process.env.NEXT_PUBLIC_ADMIN_URL || 'http://localhost:3001',
  
  // Timeouts
  REQUEST_TIMEOUT: 30000,
  DEBOUNCE_DELAY: 300,
  
  // Pagination
  DEFAULT_PAGE_SIZE: 10,
  MAX_PAGE_SIZE: 100,
  
  // Validation
  MIN_PASSWORD_LENGTH: 8,
  MAX_NAME_LENGTH: 100,
  MAX_EMAIL_LENGTH: 254,
  
  // Storage keys
  STORAGE_KEYS: {
    AUTH_TOKEN: 'auth_token',
    USER_PREFERENCES: 'user_preferences',
    THEME: 'theme',
  },
  
  // Status codes
  HTTP_STATUS: {
    OK: 200,
    CREATED: 201,
    BAD_REQUEST: 400,
    UNAUTHORIZED: 401,
    FORBIDDEN: 403,
    NOT_FOUND: 404,
    INTERNAL_SERVER_ERROR: 500,
  },
};