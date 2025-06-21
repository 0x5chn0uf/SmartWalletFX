import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';
import * as tokens from '../../../theme/generated';

const meta: Meta<typeof Button> = {
  title: 'Design System/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
A customizable button component that demonstrates design token usage.

## Design Tokens Used
- **Colors**: \`ColorBrandPrimary\`, \`ColorBrandSecondary\`, \`ColorTextPrimary\`, \`ColorTextInverse\`
- **Typography**: \`FontFamilyPrimary\`, \`FontWeightMedium\`, \`FontSizeBody\`, \`FontSizeSmall\`
- **Spacing**: \`SizeSpacingXs\`, \`SizeSpacingSm\`, \`SizeSpacingMd\`, \`SizeSpacingLg\`
- **Border Radius**: \`SizeRadiiSm\`, \`SizeRadiiMd\`, \`SizeRadiiLg\`
- **Elevation**: \`Elevation1\`

## Usage Guidelines
- Use **primary** variant for main actions
- Use **secondary** variant for alternative actions
- Use **text** variant for subtle actions
- Choose appropriate size based on context and hierarchy
        `,
      },
    },
  },
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['primary', 'secondary', 'text'],
      description: 'The visual style variant of the button',
    },
    size: {
      control: { type: 'select' },
      options: ['small', 'medium', 'large'],
      description: 'The size of the button',
    },
    disabled: {
      control: { type: 'boolean' },
      description: 'Whether the button is disabled',
    },
    children: {
      control: { type: 'text' },
      description: 'The content to display inside the button',
    },
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

// Base story with default props
export const Default: Story = {
  args: {
    children: 'Button',
    variant: 'primary',
    size: 'medium',
  },
};

// Primary variant stories
export const Primary: Story = {
  args: {
    children: 'Primary Button',
    variant: 'primary',
  },
  parameters: {
    docs: {
      description: {
        story: 'Primary buttons are used for the main action in a section or form.',
      },
    },
  },
};

export const PrimarySmall: Story = {
  args: {
    children: 'Small Primary',
    variant: 'primary',
    size: 'small',
  },
};

export const PrimaryLarge: Story = {
  args: {
    children: 'Large Primary',
    variant: 'primary',
    size: 'large',
  },
};

// Secondary variant stories
export const Secondary: Story = {
  args: {
    children: 'Secondary Button',
    variant: 'secondary',
  },
  parameters: {
    docs: {
      description: {
        story: 'Secondary buttons are used for alternative actions.',
      },
    },
  },
};

export const SecondarySmall: Story = {
  args: {
    children: 'Small Secondary',
    variant: 'secondary',
    size: 'small',
  },
};

export const SecondaryLarge: Story = {
  args: {
    children: 'Large Secondary',
    variant: 'secondary',
    size: 'large',
  },
};

// Text variant stories
export const Text: Story = {
  args: {
    children: 'Text Button',
    variant: 'text',
  },
  parameters: {
    docs: {
      description: {
        story: "Text buttons are used for subtle actions that don't need emphasis.",
      },
    },
  },
};

export const TextSmall: Story = {
  args: {
    children: 'Small Text',
    variant: 'text',
    size: 'small',
  },
};

export const TextLarge: Story = {
  args: {
    children: 'Large Text',
    variant: 'text',
    size: 'large',
  },
};

// Disabled state stories
export const Disabled: Story = {
  args: {
    children: 'Disabled Button',
    disabled: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Disabled buttons show a reduced opacity and prevent interaction.',
      },
    },
  },
};

export const DisabledPrimary: Story = {
  args: {
    children: 'Disabled Primary',
    variant: 'primary',
    disabled: true,
  },
};

export const DisabledSecondary: Story = {
  args: {
    children: 'Disabled Secondary',
    variant: 'secondary',
    disabled: true,
  },
};

export const DisabledText: Story = {
  args: {
    children: 'Disabled Text',
    variant: 'text',
    disabled: true,
  },
};

// Interactive playground
export const Playground: Story = {
  args: {
    children: 'Interactive Button',
    variant: 'primary',
    size: 'medium',
    disabled: false,
  },
  parameters: {
    docs: {
      description: {
        story: 'Use the controls below to experiment with different button configurations.',
      },
    },
  },
};

// Size comparison
export const SizeComparison: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
      <Button variant="primary" size="small">
        Small
      </Button>
      <Button variant="primary" size="medium">
        Medium
      </Button>
      <Button variant="primary" size="large">
        Large
      </Button>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Compare the different button sizes side by side.',
      },
    },
  },
};

// Variant comparison
export const VariantComparison: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
      <Button variant="primary">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="text">Text</Button>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Compare the different button variants side by side.',
      },
    },
  },
};

// Design tokens showcase
export const DesignTokensShowcase: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '400px' }}>
      <div>
        <h3 style={{ marginBottom: '8px', color: tokens.ColorTextPrimary }}>Design Token Values</h3>
        <div style={{ fontSize: tokens.FontSizeSmall, color: tokens.ColorTextSecondary }}>
          <p>Primary Color: {tokens.ColorBrandPrimary}</p>
          <p>Secondary Color: {tokens.ColorBrandSecondary}</p>
          <p>Font Family: {tokens.FontFamilyPrimary}</p>
          <p>Medium Spacing: {tokens.SizeSpacingMd}px</p>
          <p>Medium Border Radius: {tokens.SizeRadiiMd}px</p>
        </div>
      </div>
      <div style={{ display: 'flex', gap: '8px' }}>
        <Button variant="primary" size="small">
          Small
        </Button>
        <Button variant="secondary" size="medium">
          Medium
        </Button>
        <Button variant="text" size="large">
          Large
        </Button>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'This story showcases the actual design token values used in the button component.',
      },
    },
  },
};
