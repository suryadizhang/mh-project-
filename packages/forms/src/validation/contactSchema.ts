import { z } from 'zod';

/**
 * Phone number formatting regex
 * Accepts: (555) 123-4567, 555-123-4567, 5551234567, etc.
 */
const phoneRegex = /^[\d\s\-().+]+$/;

/**
 * Contact information validation schema
 */
export const contactSchema = z.object({
  name: z
    .string()
    .min(2, 'Name must be at least 2 characters')
    .max(100, 'Name must be less than 100 characters'),

  email: z
    .string()
    .email('Please enter a valid email address'),

  phone: z
    .string()
    .min(10, 'Phone number must be at least 10 digits')
    .regex(phoneRegex, 'Please enter a valid phone number'),
});

export type ContactFormData = z.infer<typeof contactSchema>;

/**
 * Partial contact schema for optional fields
 */
export const partialContactSchema = contactSchema.partial();

export type PartialContactFormData = z.infer<typeof partialContactSchema>;
