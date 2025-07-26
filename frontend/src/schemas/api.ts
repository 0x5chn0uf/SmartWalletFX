import { z } from 'zod';

// Base API Response Schema
export const ApiResponseSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({
    data: dataSchema,
    status: z.number(),
    message: z.string().optional(),
  });

// Auth-related schemas
export const UserProfileSchema = z.object({
  id: z.string(),
  username: z.string(),
  email: z.string().email(),
  email_verified: z.boolean(),
  role: z.string().optional(),
  // Profile management fields
  profile_picture_url: z.string().nullable().optional(),
  first_name: z.string().nullable().optional(),
  last_name: z.string().nullable().optional(),
  bio: z.string().nullable().optional(),
  timezone: z.string().nullable().optional(),
  preferred_currency: z.string().nullable().optional(),
  notification_preferences: z
    .object({
      email_notifications: z.boolean().optional(),
      security_alerts: z.boolean().optional(),
      portfolio_updates: z.boolean().optional(),
      price_alerts: z.boolean().optional(),
    })
    .nullable()
    .optional(),
});

// Profile update schemas
export const UserProfileUpdateSchema = z.object({
  first_name: z.string().max(100).optional(),
  last_name: z.string().max(100).optional(),
  bio: z.string().max(1000).optional(),
  timezone: z.string().max(50).optional(),
  preferred_currency: z.string().max(10).optional(),
});

export const PasswordChangeSchema = z
  .object({
    current_password: z.string().min(1, 'Current password is required'),
    new_password: z.string().min(8, 'Password must be at least 8 characters'),
    confirm_password: z.string().min(1, 'Password confirmation is required'),
  })
  .refine(data => data.new_password === data.confirm_password, {
    message: "Passwords don't match",
    path: ['confirm_password'],
  });

export const NotificationPreferencesSchema = z.object({
  email_notifications: z.boolean().optional(),
  security_alerts: z.boolean().optional(),
  portfolio_updates: z.boolean().optional(),
  price_alerts: z.boolean().optional(),
});

export const AuthErrorSchema = z.object({
  status: z.number().nullable().optional(),
  data: z.any().optional(),
  message: z.string().optional(),
});

export const TokenResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string().optional(),
});

// Auth API Response schemas
export const LoginResponseSchema = UserProfileSchema;
export const RegisterResponseSchema = z.object({
  message: z.string().optional(),
  user_id: z.string().optional(),
});
export const RefreshTokenResponseSchema = TokenResponseSchema;

// Error response schema for API errors
export const ApiErrorSchema = z.object({
  detail: z.union([
    z.string(),
    z.array(
      z.object({
        loc: z.array(z.union([z.string(), z.number()])),
        msg: z.string(),
        type: z.string(),
      })
    ),
  ]),
});

// Type exports for TypeScript
export type UserProfile = z.infer<typeof UserProfileSchema>;
export type UserProfileUpdate = z.infer<typeof UserProfileUpdateSchema>;
export type PasswordChange = z.infer<typeof PasswordChangeSchema>;
export type NotificationPreferences = z.infer<typeof NotificationPreferencesSchema>;
export type AuthError = z.infer<typeof AuthErrorSchema>;
export type TokenResponse = z.infer<typeof TokenResponseSchema>;
export type LoginResponse = z.infer<typeof LoginResponseSchema>;
export type RegisterResponse = z.infer<typeof RegisterResponseSchema>;
export type RefreshTokenResponse = z.infer<typeof RefreshTokenResponseSchema>;
export type ApiError = z.infer<typeof ApiErrorSchema>;
