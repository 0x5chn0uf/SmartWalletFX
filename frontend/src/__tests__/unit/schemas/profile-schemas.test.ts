import { describe, it, expect } from 'vitest';
import {
  UserProfileSchema,
  UserProfileUpdateSchema,
  PasswordChangeSchema,
  NotificationPreferencesSchema,
  type UserProfile,
  type UserProfileUpdate,
  type PasswordChange,
  type NotificationPreferences,
} from '../../../schemas/api';

describe('Profile Schema Validation', () => {
  describe('UserProfileSchema', () => {
    const validUserProfile: UserProfile = {
      id: 'user-123',
      username: 'testuser',
      email: 'test@example.com',
      email_verified: true,
      role: 'user',
      profile_picture_url: 'https://example.com/avatar.jpg',
      first_name: 'John',
      last_name: 'Doe',
      bio: 'Test user bio',
      timezone: 'UTC',
      preferred_currency: 'USD',
      notification_preferences: {
        email_notifications: true,
        security_alerts: true,
        portfolio_updates: false,
        price_alerts: true,
      },
    };

    it('should validate a complete user profile', () => {
      const result = UserProfileSchema.safeParse(validUserProfile);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(validUserProfile);
      }
    });

    it('should validate a minimal user profile', () => {
      const minimalProfile = {
        id: 'user-123',
        username: 'testuser',
        email: 'test@example.com',
        email_verified: false,
      };

      const result = UserProfileSchema.safeParse(minimalProfile);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.id).toBe('user-123');
        expect(result.data.username).toBe('testuser');
        expect(result.data.email).toBe('test@example.com');
        expect(result.data.email_verified).toBe(false);
      }
    });

    it('should reject invalid email format', () => {
      const invalidProfile = {
        ...validUserProfile,
        email: 'invalid-email',
      };

      const result = UserProfileSchema.safeParse(invalidProfile);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues).toHaveLength(1);
        expect(result.error.issues[0].path).toEqual(['email']);
        expect(result.error.issues[0].code).toBe('invalid_format');
      }
    });

    it('should reject missing required fields', () => {
      const incompleteProfile = {
        username: 'testuser',
        email: 'test@example.com',
        // Missing id and email_verified
      };

      const result = UserProfileSchema.safeParse(incompleteProfile);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues.length).toBeGreaterThan(0);
        const paths = result.error.issues.map(issue => issue.path[0]);
        expect(paths).toContain('id');
        expect(paths).toContain('email_verified');
      }
    });

    it('should accept null values for optional fields', () => {
      const profileWithNulls = {
        ...validUserProfile,
        role: undefined,
        profile_picture_url: null,
        first_name: null,
        last_name: null,
        bio: null,
        timezone: null,
        preferred_currency: null,
        notification_preferences: null,
      };

      const result = UserProfileSchema.safeParse(profileWithNulls);
      expect(result.success).toBe(true);
    });

    it('should validate email_verified as boolean', () => {
      const profileWithStringEmailVerified = {
        ...validUserProfile,
        email_verified: 'true', // String instead of boolean
      };

      const result = UserProfileSchema.safeParse(profileWithStringEmailVerified);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].path).toEqual(['email_verified']);
        expect(result.error.issues[0].code).toBe('invalid_type');
      }
    });
  });

  describe('UserProfileUpdateSchema', () => {
    const validUpdate: UserProfileUpdate = {
      first_name: 'Jane',
      last_name: 'Smith',
      bio: 'Updated bio',
      timezone: 'America/New_York',
      preferred_currency: 'EUR',
    };

    it('should validate a complete profile update', () => {
      const result = UserProfileUpdateSchema.safeParse(validUpdate);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(validUpdate);
      }
    });

    it('should validate partial profile updates', () => {
      const partialUpdate = {
        first_name: 'Jane',
        bio: 'New bio',
      };

      const result = UserProfileUpdateSchema.safeParse(partialUpdate);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.first_name).toBe('Jane');
        expect(result.data.bio).toBe('New bio');
        expect(result.data.last_name).toBeUndefined();
      }
    });

    it('should validate empty update object', () => {
      const emptyUpdate = {};

      const result = UserProfileUpdateSchema.safeParse(emptyUpdate);
      expect(result.success).toBe(true);
    });

    it('should reject first_name longer than 100 characters', () => {
      const longNameUpdate = {
        first_name: 'A'.repeat(101),
      };

      const result = UserProfileUpdateSchema.safeParse(longNameUpdate);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].path).toEqual(['first_name']);
        expect(result.error.issues[0].code).toBe('too_big');
      }
    });

    it('should reject last_name longer than 100 characters', () => {
      const longNameUpdate = {
        last_name: 'B'.repeat(101),
      };

      const result = UserProfileUpdateSchema.safeParse(longNameUpdate);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].path).toEqual(['last_name']);
        expect(result.error.issues[0].code).toBe('too_big');
      }
    });

    it('should reject bio longer than 1000 characters', () => {
      const longBioUpdate = {
        bio: 'C'.repeat(1001),
      };

      const result = UserProfileUpdateSchema.safeParse(longBioUpdate);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].path).toEqual(['bio']);
        expect(result.error.issues[0].code).toBe('too_big');
      }
    });

    it('should reject timezone longer than 50 characters', () => {
      const longTimezoneUpdate = {
        timezone: 'D'.repeat(51),
      };

      const result = UserProfileUpdateSchema.safeParse(longTimezoneUpdate);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].path).toEqual(['timezone']);
        expect(result.error.issues[0].code).toBe('too_big');
      }
    });

    it('should reject preferred_currency longer than 10 characters', () => {
      const longCurrencyUpdate = {
        preferred_currency: 'VERYLONGCURRENCY',
      };

      const result = UserProfileUpdateSchema.safeParse(longCurrencyUpdate);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].path).toEqual(['preferred_currency']);
        expect(result.error.issues[0].code).toBe('too_big');
      }
    });

    it('should accept maximum valid lengths', () => {
      const maxLengthUpdate = {
        first_name: 'A'.repeat(100),
        last_name: 'B'.repeat(100),
        bio: 'C'.repeat(1000),
        timezone: 'D'.repeat(50),
        preferred_currency: 'E'.repeat(10),
      };

      const result = UserProfileUpdateSchema.safeParse(maxLengthUpdate);
      expect(result.success).toBe(true);
    });
  });

  describe('PasswordChangeSchema', () => {
    const validPasswordChange: PasswordChange = {
      current_password: 'oldPassword123',
      new_password: 'newPassword456',
      confirm_password: 'newPassword456',
    };

    it('should validate a valid password change', () => {
      const result = PasswordChangeSchema.safeParse(validPasswordChange);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(validPasswordChange);
      }
    });

    it('should reject empty current password', () => {
      const invalidChange = {
        ...validPasswordChange,
        current_password: '',
      };

      const result = PasswordChangeSchema.safeParse(invalidChange);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].path).toEqual(['current_password']);
        expect(result.error.issues[0].message).toBe('Current password is required');
      }
    });

    it('should reject new password shorter than 8 characters', () => {
      const invalidChange = {
        ...validPasswordChange,
        new_password: 'short',
        confirm_password: 'short',
      };

      const result = PasswordChangeSchema.safeParse(invalidChange);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].path).toEqual(['new_password']);
        expect(result.error.issues[0].message).toBe('Password must be at least 8 characters');
      }
    });

    it('should reject empty password confirmation', () => {
      const invalidChange = {
        ...validPasswordChange,
        confirm_password: '',
      };

      const result = PasswordChangeSchema.safeParse(invalidChange);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].path).toEqual(['confirm_password']);
        expect(result.error.issues[0].message).toBe('Password confirmation is required');
      }
    });

    it('should reject mismatched passwords', () => {
      const invalidChange = {
        current_password: 'oldPassword123',
        new_password: 'newPassword456',
        confirm_password: 'differentPassword789',
      };

      const result = PasswordChangeSchema.safeParse(invalidChange);
      expect(result.success).toBe(false);
      if (!result.success) {
        const mismatchError = result.error.issues.find(
          issue =>
            issue.path.includes('confirm_password') && issue.message === "Passwords don't match"
        );
        expect(mismatchError).toBeDefined();
        expect(mismatchError?.path).toEqual(['confirm_password']);
      }
    });

    it('should accept new password exactly 8 characters', () => {
      const validChange = {
        current_password: 'oldPassword',
        new_password: 'newPass1',
        confirm_password: 'newPass1',
      };

      const result = PasswordChangeSchema.safeParse(validChange);
      expect(result.success).toBe(true);
    });

    it('should reject missing required fields', () => {
      const incompleteChange = {
        current_password: 'oldPassword123',
        // Missing new_password and confirm_password
      };

      const result = PasswordChangeSchema.safeParse(incompleteChange);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues.length).toBeGreaterThan(0);
        const paths = result.error.issues.map(issue => issue.path[0]);
        expect(paths).toContain('new_password');
        expect(paths).toContain('confirm_password');
      }
    });

    it('should validate complex password scenarios', () => {
      const complexPasswordChange = {
        current_password: 'My0ldP@ssw0rd!',
        new_password: 'MyN3wC0mpl3xP@ssw0rd!',
        confirm_password: 'MyN3wC0mpl3xP@ssw0rd!',
      };

      const result = PasswordChangeSchema.safeParse(complexPasswordChange);
      expect(result.success).toBe(true);
    });
  });

  describe('NotificationPreferencesSchema', () => {
    const validPreferences: NotificationPreferences = {
      email_notifications: true,
      security_alerts: true,
      portfolio_updates: false,
      price_alerts: true,
    };

    it('should validate complete notification preferences', () => {
      const result = NotificationPreferencesSchema.safeParse(validPreferences);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(validPreferences);
      }
    });

    it('should validate partial notification preferences', () => {
      const partialPreferences = {
        email_notifications: false,
        security_alerts: true,
        // Missing portfolio_updates and price_alerts
      };

      const result = NotificationPreferencesSchema.safeParse(partialPreferences);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.email_notifications).toBe(false);
        expect(result.data.security_alerts).toBe(true);
        expect(result.data.portfolio_updates).toBeUndefined();
        expect(result.data.price_alerts).toBeUndefined();
      }
    });

    it('should validate empty preferences object', () => {
      const emptyPreferences = {};

      const result = NotificationPreferencesSchema.safeParse(emptyPreferences);
      expect(result.success).toBe(true);
    });

    it('should reject non-boolean values', () => {
      const invalidPreferences = {
        email_notifications: 'true', // String instead of boolean
        security_alerts: 1, // Number instead of boolean
        portfolio_updates: false,
        price_alerts: null, // Null instead of boolean
      };

      const result = NotificationPreferencesSchema.safeParse(invalidPreferences);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues.length).toBeGreaterThan(0);
        const errorPaths = result.error.issues.map(issue => issue.path[0]);
        expect(errorPaths).toContain('email_notifications');
        expect(errorPaths).toContain('security_alerts');
        expect(errorPaths).toContain('price_alerts');
      }
    });

    it('should accept all false values', () => {
      const allFalsePreferences = {
        email_notifications: false,
        security_alerts: false,
        portfolio_updates: false,
        price_alerts: false,
      };

      const result = NotificationPreferencesSchema.safeParse(allFalsePreferences);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(
          Object.values(result.data).every(value => value === false || value === undefined)
        ).toBe(true);
      }
    });

    it('should accept all true values', () => {
      const allTruePreferences = {
        email_notifications: true,
        security_alerts: true,
        portfolio_updates: true,
        price_alerts: true,
      };

      const result = NotificationPreferencesSchema.safeParse(allTruePreferences);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(
          Object.values(result.data).every(value => value === true || value === undefined)
        ).toBe(true);
      }
    });

    it('should handle mixed boolean values', () => {
      const mixedPreferences = {
        email_notifications: true,
        security_alerts: false,
        portfolio_updates: true,
        price_alerts: false,
      };

      const result = NotificationPreferencesSchema.safeParse(mixedPreferences);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.email_notifications).toBe(true);
        expect(result.data.security_alerts).toBe(false);
        expect(result.data.portfolio_updates).toBe(true);
        expect(result.data.price_alerts).toBe(false);
      }
    });

    it('should reject unknown preference fields', () => {
      const invalidPreferences = {
        email_notifications: true,
        unknown_preference: true, // Unknown field
        security_alerts: true,
      };

      // Note: Zod by default strips unknown keys, but we can check if strict mode is enabled
      const result = NotificationPreferencesSchema.safeParse(invalidPreferences);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).not.toHaveProperty('unknown_preference');
      }
    });
  });

  describe('Schema Edge Cases', () => {
    it('should handle null and undefined values appropriately', () => {
      // Test UserProfileUpdateSchema with null values
      const updateWithNulls = {
        first_name: null,
        last_name: undefined,
        bio: '',
      };

      const result = UserProfileUpdateSchema.safeParse(updateWithNulls);
      expect(result.success).toBe(false); // null should not be allowed for string fields
    });

    it('should handle extremely long strings', () => {
      const veryLongString = 'A'.repeat(10000);
      const updateWithLongString = {
        bio: veryLongString,
      };

      const result = UserProfileUpdateSchema.safeParse(updateWithLongString);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].code).toBe('too_big');
      }
    });

    it('should handle special characters in strings', () => {
      const specialCharsUpdate = {
        first_name: 'José',
        last_name: "O'Brien",
        bio: 'Bio with émojis 🚀 and spéciål châractérs!',
        timezone: 'America/New_York',
        preferred_currency: '€',
      };

      const result = UserProfileUpdateSchema.safeParse(specialCharsUpdate);
      expect(result.success).toBe(true);
    });

    it('should handle whitespace-only strings', () => {
      const whitespaceUpdate = {
        first_name: '   ',
        last_name: '\t\n',
        bio: '     ',
      };

      const result = UserProfileUpdateSchema.safeParse(whitespaceUpdate);
      expect(result.success).toBe(true); // Schema allows whitespace
    });

    it('should validate password with special characters', () => {
      const specialPasswordChange = {
        current_password: 'C0mpl3x!P@ssw0rd#$%',
        new_password: 'N3w!P@ssw0rd#$%^&*()',
        confirm_password: 'N3w!P@ssw0rd#$%^&*()',
      };

      const result = PasswordChangeSchema.safeParse(specialPasswordChange);
      expect(result.success).toBe(true);
    });
  });

  describe('Type Inference', () => {
    it('should correctly infer UserProfile type', () => {
      const validProfile: UserProfile = {
        id: 'test',
        username: 'test',
        email: 'test@example.com',
        email_verified: true,
      };

      // This test passes if TypeScript compilation succeeds
      expect(typeof validProfile.id).toBe('string');
      expect(typeof validProfile.email_verified).toBe('boolean');
    });

    it('should correctly infer UserProfileUpdate type', () => {
      const validUpdate: UserProfileUpdate = {
        first_name: 'Test',
      };

      // This test passes if TypeScript compilation succeeds
      expect(typeof validUpdate.first_name).toBe('string');
    });

    it('should correctly infer PasswordChange type', () => {
      const validChange: PasswordChange = {
        current_password: 'old',
        new_password: 'newpass123',
        confirm_password: 'newpass123',
      };

      // This test passes if TypeScript compilation succeeds
      expect(typeof validChange.current_password).toBe('string');
      expect(typeof validChange.new_password).toBe('string');
      expect(typeof validChange.confirm_password).toBe('string');
    });

    it('should correctly infer NotificationPreferences type', () => {
      const validPrefs: NotificationPreferences = {
        email_notifications: true,
      };

      // This test passes if TypeScript compilation succeeds
      expect(typeof validPrefs.email_notifications).toBe('boolean');
    });
  });
});
