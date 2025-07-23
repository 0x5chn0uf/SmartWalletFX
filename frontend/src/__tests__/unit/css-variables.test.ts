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
    
    const computedStyle = getComputedStyle(testElement);
    
    // Test that CSS variables can be retrieved
    expect(computedStyle.getPropertyValue('--test-color').trim()).toBe('#2563eb');
    expect(computedStyle.getPropertyValue('--test-size').trim()).toBe('16px');
    expect(computedStyle.getPropertyValue('--test-spacing').trim()).toBe('1rem');
    
    // Test that CSS variables are applied correctly
    expect(computedStyle.color).toBe('rgb(37, 99, 235)'); // #2563eb converted
    expect(computedStyle.fontSize).toBe('16px');
    expect(computedStyle.margin).toBe('16px'); // 1rem converted to px
    
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
    
    const computedStyle = getComputedStyle(testElement);
    
    // Fallback values should be applied
    expect(computedStyle.color).toBe('rgb(255, 0, 0)'); // #ff0000
    expect(computedStyle.backgroundColor).toBe('rgb(0, 255, 0)');
    
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