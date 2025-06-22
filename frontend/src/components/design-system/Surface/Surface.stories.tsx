import type { Meta, StoryObj } from '@storybook/react';
import { Surface } from './Surface';
import * as tokens from '../../../theme/generated';

const meta: Meta<typeof Surface> = {
  title: 'Design System/Surface',
  component: Surface,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
A surface component that demonstrates background color and spacing design token usage.

## Design Tokens Used
- **Colors**: \`ColorBackgroundDefault\`, \`ColorBackgroundSurface\`, \`ColorBackgroundElevated\`
- **Typography**: \`FontFamilyPrimary\`
- **Spacing**: \`SizeSpacingSm\`, \`SizeSpacingMd\`, \`SizeSpacingLg\`
- **Border Radius**: \`SizeRadiiSm\`, \`SizeRadiiMd\`, \`SizeRadiiLg\`

## Usage Guidelines
- Use **default** for the main page background
- Use **surface** for content containers and cards
- Use **elevated** for prominent surfaces and overlays
- Choose padding based on content density
- Select border radius based on design context
        `,
      },
    },
  },
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['default', 'surface', 'elevated'],
      description: 'The background variant of the surface',
    },
    padding: {
      control: { type: 'select' },
      options: ['none', 'small', 'medium', 'large'],
      description: 'The internal padding of the surface',
    },
    borderRadius: {
      control: { type: 'select' },
      options: ['none', 'small', 'medium', 'large'],
      description: 'The border radius of the surface',
    },
    children: {
      control: { type: 'text' },
      description: 'The content to display inside the surface',
    },
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

// Base story with default props
export const Default: Story = {
  args: {
    children: 'This is a default surface with medium padding and border radius.',
    variant: 'default',
    padding: 'medium',
    borderRadius: 'medium',
  },
};

// Variant stories
export const DefaultBackground: Story = {
  args: {
    children: 'This surface uses the default background color.',
    variant: 'default',
    padding: 'medium',
    borderRadius: 'medium',
  },
  parameters: {
    docs: {
      description: {
        story: 'Default background is used for the main page background and base surfaces.',
      },
    },
  },
};

export const SurfaceBackground: Story = {
  args: {
    children: 'This surface uses the surface background color.',
    variant: 'surface',
    padding: 'medium',
    borderRadius: 'medium',
  },
  parameters: {
    docs: {
      description: {
        story: 'Surface background is used for content containers and cards.',
      },
    },
  },
};

export const ElevatedBackground: Story = {
  args: {
    children: 'This surface uses the elevated background color.',
    variant: 'elevated',
    padding: 'medium',
    borderRadius: 'medium',
  },
  parameters: {
    docs: {
      description: {
        story: 'Elevated background is used for prominent surfaces and overlays.',
      },
    },
  },
};

// Interactive playground
export const Playground: Story = {
  args: {
    children:
      'This is an interactive surface. Use the controls to experiment with different configurations.',
    variant: 'surface',
    padding: 'medium',
    borderRadius: 'medium',
  },
  parameters: {
    docs: {
      description: {
        story: 'Use the controls below to experiment with different surface configurations.',
      },
    },
  },
};

// Variant comparison
export const VariantComparison: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
      <Surface variant="default" padding="medium" borderRadius="medium">
        <h4 style={{ margin: '0 0 8px 0', color: tokens.ColorTextPrimary }}>Default</h4>
        <p style={{ margin: 0, fontSize: tokens.FontSizeSmall, color: tokens.ColorTextSecondary }}>
          Main background
        </p>
      </Surface>
      <Surface variant="surface" padding="medium" borderRadius="medium">
        <h4 style={{ margin: '0 0 8px 0', color: tokens.ColorTextPrimary }}>Surface</h4>
        <p style={{ margin: 0, fontSize: tokens.FontSizeSmall, color: tokens.ColorTextSecondary }}>
          Content container
        </p>
      </Surface>
      <Surface variant="elevated" padding="medium" borderRadius="medium">
        <h4 style={{ margin: '0 0 8px 0', color: tokens.ColorTextPrimary }}>Elevated</h4>
        <p style={{ margin: 0, fontSize: tokens.FontSizeSmall, color: tokens.ColorTextSecondary }}>
          Prominent surface
        </p>
      </Surface>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Compare the different background variants side by side.',
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
          Surface Design Token Values
        </h3>
        <div style={{ fontSize: tokens.FontSizeSmall, color: tokens.ColorTextSecondary }}>
          <p>Default Background: {tokens.ColorBackgroundDefault}</p>
          <p>Surface Background: {tokens.ColorBackgroundSurface}</p>
          <p>Elevated Background: {tokens.ColorBackgroundElevated}</p>
          <p>Medium Spacing: {tokens.SizeSpacingMd}px</p>
          <p>Medium Border Radius: {tokens.SizeRadiiMd}px</p>
        </div>
      </div>
      <div style={{ display: 'flex', gap: '8px' }}>
        <Surface variant="default" padding="small" borderRadius="small">
          Default
        </Surface>
        <Surface variant="surface" padding="small" borderRadius="small">
          Surface
        </Surface>
        <Surface variant="elevated" padding="small" borderRadius="small">
          Elevated
        </Surface>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'This story showcases the actual design token values used in the surface component.',
      },
    },
  },
};
