import { describe, it, expect } from 'vitest';
import {
  UserProfileSchema,
  AuthErrorSchema,
  TokenResponseSchema,
  LoginResponseSchema,
  RegisterResponseSchema,
  RefreshTokenResponseSchema,
  ApiErrorSchema,
} from '../../schemas/api';

describe('API Schemas', () => {
  describe('UserProfileSchema', () => {
    it('should validate a valid user profile', () => {
      const validUser = {
        id: '123',
        username: 'johndoe',
        email: 'john@example.com',
        email_verified: true,
        role: 'user',
      };

      const result = UserProfileSchema.safeParse(validUser);
      expect(result.success).toBe(true);
    });

    it('should accept user profile without optional role', () => {
      const validUser = {
        id: '123',
        username: 'johndoe',
        email: 'john@example.com',
        email_verified: false,
      };

      const result = UserProfileSchema.safeParse(validUser);
      expect(result.success).toBe(true);
    });

    it('should reject invalid email format', () => {
      const invalidUser = {
        id: '123',
        username: 'johndoe',
        email: 'invalid-email',
        email_verified: true,
      };

      const result = UserProfileSchema.safeParse(invalidUser);
      expect(result.success).toBe(false);
    });

    it('should reject missing required fields', () => {
      const invalidUser = {
        id: '123',
        email: 'john@example.com',
        // missing username and email_verified
      };

      const result = UserProfileSchema.safeParse(invalidUser);
      expect(result.success).toBe(false);
    });
  });

  describe('AuthErrorSchema', () => {
    it('should validate auth error with all fields', () => {
      const authError = {
        status: 401,
        data: { detail: 'Unauthorized' },
        message: 'Authentication failed',
      };

      const result = AuthErrorSchema.safeParse(authError);
      expect(result.success).toBe(true);
    });

    it('should validate auth error with minimal fields', () => {
      const authError = {};

      const result = AuthErrorSchema.safeParse(authError);
      expect(result.success).toBe(true);
    });

    it('should accept null status', () => {
      const authError = {
        status: null,
        message: 'Network error',
      };

      const result = AuthErrorSchema.safeParse(authError);
      expect(result.success).toBe(true);
    });
  });

  describe('TokenResponseSchema', () => {
    it('should validate token response with required fields', () => {
      const tokenResponse = {
        access_token: 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
      };

      const result = TokenResponseSchema.safeParse(tokenResponse);
      expect(result.success).toBe(true);
    });

    it('should validate token response with optional token_type', () => {
      const tokenResponse = {
        access_token: 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
        token_type: 'bearer',
      };

      const result = TokenResponseSchema.safeParse(tokenResponse);
      expect(result.success).toBe(true);
    });

    it('should reject missing access_token', () => {
      const tokenResponse = {
        token_type: 'bearer',
      };

      const result = TokenResponseSchema.safeParse(tokenResponse);
      expect(result.success).toBe(false);
    });
  });

  describe('RegisterResponseSchema', () => {
    it('should validate register response', () => {
      const registerResponse = {
        message: 'User created successfully',
        user_id: '123',
      };

      const result = RegisterResponseSchema.safeParse(registerResponse);
      expect(result.success).toBe(true);
    });

    it('should accept empty register response', () => {
      const registerResponse = {};

      const result = RegisterResponseSchema.safeParse(registerResponse);
      expect(result.success).toBe(true);
    });
  });

  describe('ApiErrorSchema', () => {
    it('should validate API error with string detail', () => {
      const apiError = {
        detail: 'Internal server error',
      };

      const result = ApiErrorSchema.safeParse(apiError);
      expect(result.success).toBe(true);
    });

    it('should validate API error with validation error array', () => {
      const apiError = {
        detail: [
          {
            loc: ['body', 'email'],
            msg: 'field required',
            type: 'value_error.missing',
          },
          {
            loc: ['body', 'password'],
            msg: 'ensure this value has at least 8 characters',
            type: 'value_error.any_str.min_length',
          },
        ],
      };

      const result = ApiErrorSchema.safeParse(apiError);
      expect(result.success).toBe(true);
    });
  });
});
