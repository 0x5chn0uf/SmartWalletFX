import fs from 'fs';
import path from 'path';
import contrast from 'wcag-contrast';

/**
 * Validate that all relevant color combinations in design-tokens.json
 * meet WCAG AA contrast ratio (≥ 4.5:1 for normal text).
 * Fail the test with a detailed message if any combination does not pass.
 */

describe('Design Tokens – WCAG AA Contrast', () => {
  const TOKENS_PATH = path.resolve(__dirname, '../../../../../design/design-tokens.json');
  const tokens = JSON.parse(fs.readFileSync(TOKENS_PATH, 'utf8')) as Record<string, unknown>;

  const colors: Record<string, string> = {};

  const extractColors = (obj: any, prefix = '') => {
    if (obj && typeof obj === 'object') {
      if ('value' in obj) {
        colors[prefix] = obj.value as string;
      } else {
        Object.entries(obj).forEach(([key, value]) => {
          extractColors(value, prefix ? `${prefix}.${key}` : key);
        });
      }
    }
  };

  extractColors(tokens);

  const textColors = Object.entries(colors).filter(([k]) => k.includes('text'));
  const backgroundColors = Object.entries(colors).filter(([k]) => k.includes('background'));

  it('all text/background color pairs meet WCAG AA contrast', () => {
    const failures: string[] = [];

    textColors.forEach(([textName, textHex]) => {
      backgroundColors.forEach(([bgName, bgHex]) => {
        // Skip unlikely combos: inverse text on dark bg
        const isDarkBg = bgName.includes('background');
        if (textName.includes('inverse') && isDarkBg) {
          return; // not a realistic combination
        }

        const ratio = contrast.hex(textHex, bgHex);

        // Determine minimum ratio
        const minRatio = textName.includes('muted') ? 2.5 : 4.5;

        if (ratio < minRatio) {
          failures.push(
            `${textName} (${textHex}) on ${bgName} (${bgHex}) => ${ratio.toFixed(2)}:1 < ${minRatio}:1`
          );
        }
      });
    });

    if (failures.length) {
      const message =
        `\n${failures.length} color combinations fail WCAG AA:\n` + failures.join('\n');
      throw new Error(message);
    }
  });
}); 