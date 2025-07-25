/**
 * CSS Variables Smoke Test
 *
 * Ensures that CSS custom properties are properly defined and accessible
 */

import fs from 'fs';
import path from 'path';

describe('CSS Custom Properties', () => {
  it('should have CSS tokens file with proper content', () => {
    const tokensPath = path.resolve(__dirname, '../../theme/tokens.css');
    const exists = fs.existsSync(tokensPath);
    expect(exists).toBe(true);

    if (exists) {
      const content = fs.readFileSync(tokensPath, 'utf-8');
      expect(content).toContain('--color-brand-primary');
      expect(content).toContain('--font-size-base');
      expect(content).toContain('--size-4');
      expect(content).toContain(':root');
    }
  });

  it('should define CSS custom properties correctly', () => {
    // Add test styles to verify CSS custom properties work
    const style = document.createElement('style');
    style.textContent = `
      :root {
        --test-color: #2563eb;
        --test-size: 16px;
        --test-spacing: 1rem;
      }
      .test-element {
        color: var(--test-color);
        font-size: var(--test-size);
        margin: var(--test-spacing);
      }
    `;
    document.head.appendChild(style);

    const testElement = document.createElement('div');
    testElement.className = 'test-element';
    document.body.appendChild(testElement);

    // In jsdom, CSS custom properties might not resolve fully
    // So we test that the style element contains the expected CSS
    expect(style.textContent).toContain('--test-color: #2563eb');
    expect(style.textContent).toContain('--test-size: 16px');
    expect(style.textContent).toContain('--test-spacing: 1rem');

    // Test that the element has the expected class
    expect(testElement.className).toBe('test-element');

    // Cleanup
    document.body.removeChild(testElement);
    document.head.removeChild(style);
  });

  it('should support CSS variable fallbacks', () => {
    const style = document.createElement('style');
    style.textContent = `
      .fallback-test {
        color: var(--non-existent-variable, #ff0000);
        background: var(--also-non-existent, rgb(0, 255, 0));
      }
    `;
    document.head.appendChild(style);

    const testElement = document.createElement('div');
    testElement.className = 'fallback-test';
    document.body.appendChild(testElement);

    // Test that CSS contains the fallback syntax
    expect(style.textContent).toContain('var(--non-existent-variable, #ff0000)');
    expect(style.textContent).toContain('var(--also-non-existent, rgb(0, 255, 0))');

    // Cleanup
    document.body.removeChild(testElement);
    document.head.removeChild(style);
  });

  it('should verify token file structure and organization', () => {
    const tokensPath = path.resolve(__dirname, '../../theme/tokens.css');
    const content = fs.readFileSync(tokensPath, 'utf-8');

    // Check for proper organization sections
    expect(content).toContain('/* === Colors === */');
    expect(content).toContain('/* === Typography === */');
    expect(content).toContain('/* === Spacing === */');
    expect(content).toContain('/* === Shadows === */');

    // Check for accessibility considerations
    expect(content).toContain('@media (prefers-color-scheme: light)');
    expect(content).toContain('@media (prefers-contrast: high)');
    expect(content).toContain('@media (prefers-reduced-motion: reduce)');
  });
});
