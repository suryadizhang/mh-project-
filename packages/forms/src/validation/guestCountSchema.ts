import { z } from 'zod';

/**
 * Guest count validation schema (single count)
 */
export const guestCountSchema = z.object({
  guestCount: z
    .number()
    .min(1, 'At least 1 guest is required')
    .max(100, 'Maximum 100 guests allowed'),
});

export type GuestCountFormData = z.infer<typeof guestCountSchema>;

/**
 * Guest count with adults/children split
 */
export const guestCountSplitSchema = z
  .object({
    adults: z
      .number()
      .min(1, 'At least 1 adult is required')
      .max(50, 'Maximum 50 adults'),

    children: z
      .number()
      .min(0, 'Cannot be negative')
      .max(30, 'Maximum 30 children'),
  })
  .refine(data => data.adults + data.children >= 10, {
    message: 'Minimum 10 guests required for hibachi service',
  });

export type GuestCountSplitFormData = z.infer<typeof guestCountSplitSchema>;

/**
 * Flexible guest count (works with both patterns)
 */
export const flexibleGuestCountSchema = z.union([
  guestCountSchema,
  guestCountSplitSchema,
]);

export type FlexibleGuestCountFormData = z.infer<
  typeof flexibleGuestCountSchema
>;
