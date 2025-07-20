import { z, ZodError } from 'zod';
import { AxiosResponse } from 'axios';

// Custom error class for validation failures
export class ValidationError extends Error {
  public readonly zodError: ZodError;
  public readonly response: AxiosResponse;

  constructor(zodError: ZodError, response: AxiosResponse, message?: string) {
    super(message || `Validation failed: ${zodError.message}`);
    this.name = 'ValidationError';
    this.zodError = zodError;
    this.response = response;
  }
}

// Generic validation function for API responses
export function validateApiResponse<T>(response: AxiosResponse, schema: z.ZodSchema<T>): T {
  try {
    return schema.parse(response.data);
  } catch (error) {
    if (error instanceof ZodError) {
      console.error('API Response validation failed:', {
        url: response.config?.url,
        status: response.status,
        zodError: error.errors,
        receivedData: response.data,
      });
      throw new ValidationError(error, response);
    }
    throw error;
  }
}

// Wrapper function for API calls with validation
export async function validateApiCall<T>(
  apiCall: () => Promise<AxiosResponse>,
  schema: z.ZodSchema<T>
): Promise<T> {
  const response = await apiCall();
  return validateApiResponse(response, schema);
}

// Safe parse function that returns either success or error
export function safeValidateApiResponse<T>(
  response: AxiosResponse,
  schema: z.ZodSchema<T>
): { success: true; data: T } | { success: false; error: ZodError; response: AxiosResponse } {
  const result = schema.safeParse(response.data);

  if (result.success) {
    return { success: true, data: result.data };
  }

  console.error('API Response validation failed (safe):', {
    url: response.config?.url,
    status: response.status,
    zodError: result.error.errors,
    receivedData: response.data,
  });

  return { success: false, error: result.error, response };
}

// Utility to format validation errors for user display
export function formatValidationError(error: ValidationError): string {
  const issues = error.zodError.errors.map(err => {
    const path = err.path.length > 0 ? ` at ${err.path.join('.')}` : '';
    return `${err.message}${path}`;
  });

  return `Response validation failed: ${issues.join(', ')}`;
}
