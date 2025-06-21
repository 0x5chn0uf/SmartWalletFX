import type { Meta, StoryObj } from '@storybook/react';
import { Card } from './Card';
import * as tokens from '../../../theme/generated';

const meta: Meta<typeof Card> = {
  title: 'Design System/Card',
  component: Card,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
A flexible card component that demonstrates surface design token usage.

## Design Tokens Used
- **Colors**: \`ColorBackgroundSurface\`, \`ColorBackgroundElevated\`
- **Typography**: \`FontFamilyPrimary\`
- **Spacing**: \`SizeSpacingSm\`, \`SizeSpacingMd\`, \`SizeSpacingLg\`
- **Border Radius**: \`SizeRadiiMd\`
- **Elevation**: \`Elevation1\`, \`Elevation2\`, \`Elevation3\`, \`Elevation4\`

## Usage Guidelines
- Use **none** elevation for flat surfaces
- Use **low** elevation for subtle depth
- Use **medium** elevation for standard cards
- Use **high** elevation for prominent surfaces
- Choose padding based on content density and hierarchy
        `,
      },
    },
  },
  argTypes: {
    elevation: {
      control: { type: 'select' },
      options: ['none', 'low', 'medium', 'high'],
      description: 'The elevation level of the card',
    },
    padding: {
      control: { type: 'select' },
      options: ['none', 'small', 'medium', 'large'],
      description: 'The internal padding of the card',
    },
    children: {
      control: { type: 'text' },
      description: 'The content to display inside the card',
    },
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

// Base story with default props
export const Default: Story = {
  args: {
    children: 'This is a default card with medium elevation and padding.',
    elevation: 'medium',
    padding: 'medium',
  },
};

// Elevation variations
export const NoElevation: Story = {
  args: {
    children: 'This card has no elevation - it appears flat.',
    elevation: 'none',
    padding: 'medium',
  },
  parameters: {
    docs: {
      description: {
        story: 'Cards with no elevation appear flat and blend with the background.',
      },
    },
  },
};

export const LowElevation: Story = {
  args: {
    children: 'This card has low elevation for subtle depth.',
    elevation: 'low',
    padding: 'medium',
  },
  parameters: {
    docs: {
      description: {
        story: 'Low elevation provides subtle depth without being prominent.',
      },
    },
  },
};

export const HighElevation: Story = {
  args: {
    children: 'This card has high elevation for prominent display.',
    elevation: 'high',
    padding: 'medium',
  },
  parameters: {
    docs: {
      description: {
        story: 'High elevation makes the card stand out prominently from the background.',
      },
    },
  },
};

// Padding variations
export const NoPadding: Story = {
  args: {
    children: 'This card has no internal padding.',
    elevation: 'medium',
    padding: 'none',
  },
  parameters: {
    docs: {
      description: {
        story: 'Cards with no padding allow content to extend to the edges.',
      },
    },
  },
};

export const SmallPadding: Story = {
  args: {
    children: 'This card has small padding for compact content.',
    elevation: 'medium',
    padding: 'small',
  },
  parameters: {
    docs: {
      description: {
        story: 'Small padding is ideal for compact content or dense layouts.',
      },
    },
  },
};

export const LargePadding: Story = {
  args: {
    children: 'This card has large padding for spacious content.',
    elevation: 'medium',
    padding: 'large',
  },
  parameters: {
    docs: {
      description: {
        story: 'Large padding provides breathing room for content.',
      },
    },
  },
};

// Interactive playground
export const Playground: Story = {
  args: {
    children:
      'This is an interactive card. Use the controls to experiment with different configurations.',
    elevation: 'medium',
    padding: 'medium',
  },
  parameters: {
    docs: {
      description: {
        story: 'Use the controls below to experiment with different card configurations.',
      },
    },
  },
};

// Elevation comparison
export const ElevationComparison: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
      <Card elevation="none" padding="medium">
        <h4 style={{ margin: '0 0 8px 0', color: tokens.ColorTextPrimary }}>None</h4>
        <p style={{ margin: 0, fontSize: tokens.FontSizeSmall, color: tokens.ColorTextSecondary }}>
          Flat surface
        </p>
      </Card>
      <Card elevation="low" padding="medium">
        <h4 style={{ margin: '0 0 8px 0', color: tokens.ColorTextPrimary }}>Low</h4>
        <p style={{ margin: 0, fontSize: tokens.FontSizeSmall, color: tokens.ColorTextSecondary }}>
          Subtle depth
        </p>
      </Card>
      <Card elevation="medium" padding="medium">
        <h4 style={{ margin: '0 0 8px 0', color: tokens.ColorTextPrimary }}>Medium</h4>
        <p style={{ margin: 0, fontSize: tokens.FontSizeSmall, color: tokens.ColorTextSecondary }}>
          Standard card
        </p>
      </Card>
      <Card elevation="high" padding="medium">
        <h4 style={{ margin: '0 0 8px 0', color: tokens.ColorTextPrimary }}>High</h4>
        <p style={{ margin: 0, fontSize: tokens.FontSizeSmall, color: tokens.ColorTextSecondary }}>
          Prominent surface
        </p>
      </Card>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Compare the different elevation levels side by side.',
      },
    },
  },
};

// Padding comparison
export const PaddingComparison: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
      <Card elevation="medium" padding="none">
        <h4 style={{ margin: '0 0 8px 0', color: tokens.ColorTextPrimary }}>No Padding</h4>
        <p style={{ margin: 0, fontSize: tokens.FontSizeSmall, color: tokens.ColorTextSecondary }}>
          Content extends to edges
        </p>
      </Card>
      <Card elevation="medium" padding="small">
        <h4 style={{ margin: '0 0 8px 0', color: tokens.ColorTextPrimary }}>Small</h4>
        <p style={{ margin: 0, fontSize: tokens.FontSizeSmall, color: tokens.ColorTextSecondary }}>
          Compact spacing
        </p>
      </Card>
      <Card elevation="medium" padding="medium">
        <h4 style={{ margin: '0 0 8px 0', color: tokens.ColorTextPrimary }}>Medium</h4>
        <p style={{ margin: 0, fontSize: tokens.FontSizeSmall, color: tokens.ColorTextSecondary }}>
          Standard spacing
        </p>
      </Card>
      <Card elevation="medium" padding="large">
        <h4 style={{ margin: '0 0 8px 0', color: tokens.ColorTextPrimary }}>Large</h4>
        <p style={{ margin: 0, fontSize: tokens.FontSizeSmall, color: tokens.ColorTextSecondary }}>
          Spacious layout
        </p>
      </Card>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Compare the different padding levels side by side.',
      },
    },
  },
};

// Content examples
export const ContentExample: Story = {
  render: () => (
    <Card elevation="medium" padding="medium" style={{ maxWidth: '400px' }}>
      <h3
        style={{
          margin: '0 0 16px 0',
          color: tokens.ColorTextPrimary,
          fontSize: tokens.FontSizeH2,
        }}
      >
        Card Title
      </h3>
      <p
        style={{
          margin: '0 0 16px 0',
          color: tokens.ColorTextSecondary,
          lineHeight: tokens.FontLineheightBody,
        }}
      >
        This is an example of a card with rich content including a title, description, and action
        buttons.
      </p>
      <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
        <button
          style={{
            padding: `${tokens.SizeSpacingXs}px ${tokens.SizeSpacingSm}px`,
            fontSize: tokens.FontSizeSmall,
            borderRadius: tokens.SizeRadiiSm,
            border: 'none',
            backgroundColor: 'transparent',
            color: tokens.ColorBrandPrimary,
            cursor: 'pointer',
          }}
        >
          Cancel
        </button>
        <button
          style={{
            padding: `${tokens.SizeSpacingXs}px ${tokens.SizeSpacingSm}px`,
            fontSize: tokens.FontSizeSmall,
            borderRadius: tokens.SizeRadiiSm,
            border: 'none',
            backgroundColor: tokens.ColorBrandPrimary,
            color: tokens.ColorTextInverse,
            cursor: 'pointer',
          }}
        >
          Save
        </button>
      </div>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'An example of a card with rich content including title, description, and action buttons.',
      },
    },
  },
};

// Design tokens showcase
export const DesignTokensShowcase: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '500px' }}>
      <div>
        <h3 style={{ marginBottom: '8px', color: tokens.ColorTextPrimary }}>
          Card Design Token Values
        </h3>
        <div style={{ fontSize: tokens.FontSizeSmall, color: tokens.ColorTextSecondary }}>
          <p>Surface Background: {tokens.ColorBackgroundSurface}</p>
          <p>Elevated Background: {tokens.ColorBackgroundElevated}</p>
          <p>Medium Border Radius: {tokens.SizeRadiiMd}px</p>
          <p>Medium Spacing: {tokens.SizeSpacingMd}px</p>
          <p>Elevation 1: {tokens.Elevation1}</p>
          <p>Elevation 2: {tokens.Elevation2}</p>
          <p>Elevation 4: {tokens.Elevation4}</p>
        </div>
      </div>
      <div style={{ display: 'flex', gap: '8px' }}>
        <Card elevation="none" padding="small">
          None
        </Card>
        <Card elevation="low" padding="small">
          Low
        </Card>
        <Card elevation="medium" padding="small">
          Medium
        </Card>
        <Card elevation="high" padding="small">
          High
        </Card>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'This story showcases the actual design token values used in the card component.',
      },
    },
  },
};
