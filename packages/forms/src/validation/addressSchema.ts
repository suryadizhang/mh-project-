import { z } from 'zod';

/**
 * ZIP code regex - 5 digits or 5+4 format
 */
const zipCodeRegex = /^[0-9]{5}(-[0-9]{4})?$/;

/**
 * Address validation schema
 */
export const addressSchema = z.object({
  street: z
    .string()
    .min(5, 'Please enter a valid street address')
    .max(200, 'Address is too long'),

  city: z
    .string()
    .min(2, 'City is required')
    .max(100, 'City name is too long'),

  state: z
    .string()
    .length(2, 'Please select a state'),

  zipcode: z
    .string()
    .regex(zipCodeRegex, 'Please enter a valid ZIP code'),
});

export type AddressFormData = z.infer<typeof addressSchema>;

/**
 * Venue address with optional coordinates
 */
export const venueAddressSchema = addressSchema.extend({
  lat: z.number().optional(),
  lng: z.number().optional(),
  normalized: z.string().optional(),
});

export type VenueAddressFormData = z.infer<typeof venueAddressSchema>;

/**
 * Billing address with "same as venue" option
 */
export const billingAddressSchema = addressSchema.extend({
  sameAsVenue: z.boolean().optional(),
}).refine(
  (data) => {
    // If sameAsVenue is true, other fields are not required
    if (data.sameAsVenue) return true;
    // Otherwise, all fields must be present
    return data.street && data.city && data.state && data.zipcode;
  },
  { message: 'Please enter billing address or select "Same as venue"' }
);

export type BillingAddressFormData = z.infer<typeof billingAddressSchema>;
