import { describe, it, expect, vi } from 'vitest';
import { AxiosResponse } from 'axios';
import { z } from 'zod';
import {
  validateApiResponse,
  ValidationError,
  safeValidateApiResponse,
  formatValidationError,
} from '../../utils/validation';

describe('API Validation Utils', () => {
  const mockResponse = (data: any, status = 200): AxiosResponse => ({
    data,
    status,
    statusText: 'OK',
    headers: {},
    config: { url: '/api/test' } as any,
  });

  const testSchema = z.object({
    id: z.string(),
    name: z.string(),
    email: z.string().email(),
  });

  describe('validateApiResponse', () => {
    it('should validate and return data when schema matches', () => {
      const validData = {
        id: '123',
        name: 'John Doe',
        email: 'john@example.com',
      };
      const response = mockResponse(validData);

      const result = validateApiResponse(response, testSchema);
      expect(result).toEqual(validData);
    });

    it('should throw ValidationError when schema does not match', () => {
      const invalidData = {
        id: '123',
        name: 'John Doe',
        email: 'invalid-email', // invalid email format
      };
      const response = mockResponse(invalidData);

      expect(() => validateApiResponse(response, testSchema)).toThrow(ValidationError);
    });

    it('should include response data in ValidationError', () => {
      const invalidData = { id: 123 }; // wrong type
      const response = mockResponse(invalidData);

      try {
        validateApiResponse(response, testSchema);
      } catch (error) {
        expect(error).toBeInstanceOf(ValidationError);
        expect((error as ValidationError).response).toBe(response);
        expect((error as ValidationError).zodError).toBeDefined();
      }
    });
  });

  describe('safeValidateApiResponse', () => {
    it('should return success object when validation passes', () => {
      const validData = {
        id: '123',
        name: 'John Doe',
        email: 'john@example.com',
      };
      const response = mockResponse(validData);

      const result = safeValidateApiResponse(response, testSchema);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(validData);
      }
    });

    it('should return error object when validation fails', () => {
      const invalidData = {
        id: '123',
        name: 'John Doe',
        email: 'invalid-email',
      };
      const response = mockResponse(invalidData);

      const result = safeValidateApiResponse(response, testSchema);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toBeDefined();
        expect(result.response).toBe(response);
      }
    });
  });

  describe('formatValidationError', () => {
    it('should format validation error messages nicely', () => {
      const invalidData = {
        id: 123, // wrong type
        name: '', // empty string
        email: 'invalid-email',
      };
      const response = mockResponse(invalidData);

      try {
        validateApiResponse(response, testSchema);
      } catch (error) {
        if (error instanceof ValidationError) {
          const formatted = formatValidationError(error);
          expect(formatted).toContain('Response validation failed');
          expect(typeof formatted).toBe('string');
        }
      }
    });
  });

  describe('console error logging', () => {
    it('should log validation errors to console', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const invalidData = { id: 123 };
      const response = mockResponse(invalidData);

      try {
        validateApiResponse(response, testSchema);
      } catch (error) {
        // Error should be logged
      }

      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });

    it('should log validation errors in safe validation', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const invalidData = { id: 123 };
      const response = mockResponse(invalidData);

      safeValidateApiResponse(response, testSchema);

      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });
});
