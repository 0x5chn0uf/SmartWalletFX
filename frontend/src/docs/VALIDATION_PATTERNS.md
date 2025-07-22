# API Response Validation Patterns

This document outlines the runtime validation patterns implemented for API responses using Zod in the frontend application.

## Overview

Runtime validation ensures that API responses match expected TypeScript types, providing:
- **Runtime type safety** beyond compile-time TypeScript checking
- **Better error handling** with detailed validation error messages  
- **Developer experience** with clear error logging and debugging info
- **Production reliability** by catching unexpected API response formats

## Architecture

### Core Components

1. **Zod Schemas** (`src/schemas/`)
   - Define expected response structures
   - Generate TypeScript types automatically
   - Validate data at runtime

2. **Validation Utilities** (`src/utils/validation.ts`)
   - Wrapper functions for API validation
   - Error handling and logging
   - Safe validation methods

3. **Validated Services** (`src/services/`)
   - API service functions using validation
   - Type-safe response handling

## Usage Patterns

### 1. Basic API Response Validation

```typescript
import { validateApiResponse } from '../utils/validation';
import { UserProfileSchema } from '../schemas/api';

export async function getUserProfile(): Promise<UserProfile> {
  const response = await apiClient.get('/users/me');
  return validateApiResponse(response, UserProfileSchema);
}
```

### 2. Safe Validation (Non-throwing)

```typescript
import { safeValidateApiResponse } from '../utils/validation';
import { WalletListSchema } from '../schemas/wallet';

export async function getWalletsSafely() {
  const response = await apiClient.get('/defi/wallets');
  const result = safeValidateApiResponse(response, WalletListSchema);
  
  if (result.success) {
    return result.data;
  } else {
    console.error('Validation failed:', result.error);
    return [];
  }
}
```

### 3. Redux Async Thunk with Validation

```typescript
import { createAsyncThunk } from '@reduxjs/toolkit';
import { validateApiResponse, ValidationError } from '../utils/validation';
import { UserProfileSchema } from '../schemas/api';

export const fetchCurrentUser = createAsyncThunk(
  'auth/fetchCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      const resp = await apiClient.get('/users/me');
      return validateApiResponse(resp, UserProfileSchema);
    } catch (err) {
      if (err instanceof ValidationError) {
        return rejectWithValue({
          status: err.response.status,
          message: formatValidationError(err),
        });
      }
      throw err;
    }
  }
);
```

## Schema Definitions

### Auth Schemas (`src/schemas/api.ts`)

```typescript
export const UserProfileSchema = z.object({
  id: z.string(),
  username: z.string(),
  email: z.string().email(),
  email_verified: z.boolean(),
  role: z.string().optional(),
});

export const TokenResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string().optional(),
});
```

### Wallet Schemas (`src/schemas/wallet.ts`)

```typescript
export const WalletDetailsSchema = z.object({
  address: z.string(),
  name: z.string().optional(),
  balance: z.string(),
  token: z.string(),
  usd_value: z.number().optional(),
  portfolio_percentage: z.number().optional(),
});

export const TransactionSchema = z.object({
  id: z.string(),
  hash: z.string(),
  from: z.string(),
  to: z.string(),
  value: z.string(),
  timestamp: z.number(),
  status: z.enum(['pending', 'confirmed', 'failed']),
  gas_used: z.string().optional(),
  gas_price: z.string().optional(),
});
```

## Error Handling

### Validation Errors

The `ValidationError` class provides detailed information about validation failures:

```typescript
try {
  return validateApiResponse(response, schema);
} catch (error) {
  if (error instanceof ValidationError) {
    // Access zodError for detailed validation info
    console.error('Validation failed:', error.zodError.errors);
    
    // Access original response for debugging
    console.error('Response data:', error.response.data);
    
    // Get formatted error message
    const message = formatValidationError(error);
  }
}
```

### Logging

Validation errors are automatically logged with context:

```json
{
  "url": "/api/users/me",
  "status": 200,
  "zodError": [
    {
      "code": "invalid_type",
      "expected": "string",
      "received": "number",
      "path": ["id"],
      "message": "Expected string, received number"
    }
  ],
  "receivedData": { "id": 123, "email": "user@example.com" }
}
```

## Testing

### Schema Tests

```typescript
describe('UserProfileSchema', () => {
  it('should validate valid user profile', () => {
    const validUser = {
      id: '123',
      username: 'johndoe',
      email: 'john@example.com',
      email_verified: true,
    };
    
    const result = UserProfileSchema.safeParse(validUser);
    expect(result.success).toBe(true);
  });
});
```

### Integration Tests

```typescript
describe('getWallets with validation', () => {
  it('should return validated wallet list', async () => {
    const validData = ['0x123...', '0xabc...'];
    mockedApi.get.mockResolvedValue({ data: validData });
    
    const result = await getWallets();
    expect(result).toEqual(validData);
  });

  it('should throw ValidationError for invalid data', async () => {
    const invalidData = [123, 'valid-address']; // mixed types
    mockedApi.get.mockResolvedValue({ data: invalidData });
    
    await expect(getWallets()).rejects.toThrow(ValidationError);
  });
});
```

## Best Practices

### 1. Schema Design

- **Use optional fields** for data that may not always be present
- **Define enums** for known string values (e.g., transaction status)
- **Validate email formats** using `z.string().email()`
- **Use specific types** (e.g., `z.number()` for numeric IDs when appropriate)

### 2. Error Handling

- **Always handle ValidationError** in API calls
- **Log validation errors** with context for debugging
- **Provide fallback values** for non-critical data
- **Pass validation errors to error boundaries** in UI components

### 3. Performance

- **Reuse schema instances** - don't recreate schemas in loops
- **Use safe parsing** for performance-critical paths where errors are expected
- **Consider caching** validated responses for expensive operations

### 4. Type Safety

- **Export both schemas and types** from schema files
- **Use generated types** in component props and state
- **Avoid any types** - leverage Zod's type inference

## Migration Guide

When adding validation to existing API endpoints:

1. **Create Zod schema** based on existing TypeScript interface
2. **Add validation** to service function
3. **Update error handling** in calling code
4. **Write tests** for schema and service integration
5. **Monitor logs** for validation failures in production

## Future Considerations

- **Response caching** with validation
- **Partial validation** for streaming endpoints
- **Schema versioning** for API evolution
- **Performance monitoring** for validation overhead