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
export type AuthError = z.infer<typeof AuthErrorSchema>;
export type TokenResponse = z.infer<typeof TokenResponseSchema>;
export type LoginResponse = z.infer<typeof LoginResponseSchema>;
export type RegisterResponse = z.infer<typeof RegisterResponseSchema>;
export type RefreshTokenResponse = z.infer<typeof RefreshTokenResponseSchema>;
export type ApiError = z.infer<typeof ApiErrorSchema>;
