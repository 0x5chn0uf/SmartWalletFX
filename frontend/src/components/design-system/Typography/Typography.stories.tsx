import type { Meta, StoryObj } from '@storybook/react';
import { Typography } from './Typography';
import * as tokens from '../../../theme/generated';

const meta: Meta<typeof Typography> = {
  title: 'Design System/Typography',
  component: Typography,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
A typography component that demonstrates typography design token usage.

## Design Tokens Used
- **Typography**: \`FontFamilyPrimary\`, \`FontWeightRegular\`, \`FontWeightMedium\`, \`FontWeightSemibold\`, \`FontWeightBold\`
- **Font Sizes**: \`FontSizeDisplay\`, \`FontSizeH1\`, \`FontSizeH2\`, \`FontSizeBody\`, \`FontSizeCaption\`, \`FontSizeSmall\`
- **Line Heights**: \`FontLineheightDisplay\`, \`FontLineheightHeading\`, \`FontLineheightBody\`
- **Colors**: \`ColorTextPrimary\`

## Usage Guidelines
- Use **display** for hero text and large headlines
- Use **h1** for main page headings
- Use **h2** for section headings
- Use **body** for main content text
- Use **caption** for supporting text and labels
- Use **small** for fine print and metadata
- Choose appropriate weight based on hierarchy and emphasis
        `,
      },
    },
  },
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['display', 'h1', 'h2', 'body', 'caption', 'small'],
      description: 'The typography variant',
    },
    weight: {
      control: { type: 'select' },
      options: ['regular', 'medium', 'semibold', 'bold'],
      description: 'The font weight',
    },
    children: {
      control: { type: 'text' },
      description: 'The text content',
    },
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

// Base story with default props
export const Default: Story = {
  args: {
    children: 'This is default typography with body variant and regular weight.',
    variant: 'body',
    weight: 'regular',
  },
};

// Variant stories
export const Display: Story = {
  args: {
    children: 'Display Text',
    variant: 'display',
    weight: 'bold',
  },
  parameters: {
    docs: {
      description: {
        story: 'Display text is used for hero headlines and large, impactful text.',
      },
    },
  },
};

export const Heading1: Story = {
  args: {
    children: 'Heading 1',
    variant: 'h1',
    weight: 'bold',
  },
  parameters: {
    docs: {
      description: {
        story: 'H1 is used for main page headings and primary titles.',
      },
    },
  },
};

export const Heading2: Story = {
  args: {
    children: 'Heading 2',
    variant: 'h2',
    weight: 'semibold',
  },
  parameters: {
    docs: {
      description: {
        story: 'H2 is used for section headings and secondary titles.',
      },
    },
  },
};

export const Body: Story = {
  args: {
    children:
      'This is body text used for main content. It provides good readability for longer passages of text.',
    variant: 'body',
    weight: 'regular',
  },
  parameters: {
    docs: {
      description: {
        story: 'Body text is the standard for main content and provides optimal readability.',
      },
    },
  },
};

export const Caption: Story = {
  args: {
    children: 'This is caption text used for supporting information and labels.',
    variant: 'caption',
    weight: 'regular',
  },
  parameters: {
    docs: {
      description: {
        story: 'Caption text is used for supporting information, labels, and secondary content.',
      },
    },
  },
};

export const Small: Story = {
  args: {
    children: 'This is small text used for fine print, metadata, and secondary information.',
    variant: 'small',
    weight: 'regular',
  },
  parameters: {
    docs: {
      description: {
        story: 'Small text is used for fine print, metadata, and secondary information.',
      },
    },
  },
};

// Weight variations
export const RegularWeight: Story = {
  args: {
    children: 'Regular weight text',
    variant: 'body',
    weight: 'regular',
  },
};

export const MediumWeight: Story = {
  args: {
    children: 'Medium weight text',
    variant: 'body',
    weight: 'medium',
  },
};

export const SemiboldWeight: Story = {
  args: {
    children: 'Semibold weight text',
    variant: 'body',
    weight: 'semibold',
  },
};

export const BoldWeight: Story = {
  args: {
    children: 'Bold weight text',
    variant: 'body',
    weight: 'bold',
  },
};

// Interactive playground
export const Playground: Story = {
  args: {
    children:
      'Interactive typography. Use the controls to experiment with different configurations.',
    variant: 'body',
    weight: 'regular',
  },
  parameters: {
    docs: {
      description: {
        story: 'Use the controls below to experiment with different typography configurations.',
      },
    },
  },
};

// Typography scale
export const TypographyScale: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '600px' }}>
      <Typography variant="display" weight="bold">
        Display Text (48px)
      </Typography>
      <Typography variant="h1" weight="bold">
        Heading 1 (36px)
      </Typography>
      <Typography variant="h2" weight="semibold">
        Heading 2 (24px)
      </Typography>
      <Typography variant="body" weight="regular">
        Body Text (16px) - This is the standard text size for main content. It provides good
        readability for longer passages of text and is the foundation of our typography system.
      </Typography>
      <Typography variant="caption" weight="regular">
        Caption Text (14px) - Used for supporting information, labels, and secondary content that
        needs to be slightly smaller than body text.
      </Typography>
      <Typography variant="small" weight="regular">
        Small Text (12px) - Used for fine print, metadata, and secondary information that needs to
        be compact.
      </Typography>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'The complete typography scale showing all available variants.',
      },
    },
  },
};

// Weight comparison
export const WeightComparison: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxWidth: '400px' }}>
      <Typography variant="body" weight="regular">
        Regular weight (400) - Standard text weight
      </Typography>
      <Typography variant="body" weight="medium">
        Medium weight (500) - Slightly emphasized text
      </Typography>
      <Typography variant="body" weight="semibold">
        Semibold weight (600) - More emphasized text
      </Typography>
      <Typography variant="body" weight="bold">
        Bold weight (700) - Strongly emphasized text
      </Typography>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Compare the different font weights side by side.',
      },
    },
  },
};

// Content examples
export const ContentExample: Story = {
  render: () => (
    <div style={{ maxWidth: '500px' }}>
      <Typography variant="h1" weight="bold" style={{ marginBottom: '16px' }}>
        Article Title
      </Typography>
      <Typography variant="body" weight="regular" style={{ marginBottom: '16px' }}>
        This is the introduction paragraph that sets the context for the article. It uses body text
        with regular weight for optimal readability.
      </Typography>
      <Typography
        variant="h2"
        weight="semibold"
        style={{ marginBottom: '12px', marginTop: '24px' }}
      >
        Section Heading
      </Typography>
      <Typography variant="body" weight="regular" style={{ marginBottom: '16px' }}>
        This is the main content section. It demonstrates how typography creates visual hierarchy
        and improves readability. The combination of different variants and weights helps guide the
        reader through the content.
      </Typography>
      <Typography variant="caption" weight="regular" style={{ color: tokens.ColorTextSecondary }}>
        Published on June 22, 2025 • 5 min read
      </Typography>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'An example of typography in a real content context showing hierarchy and readability.',
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
          Typography Design Token Values
        </h3>
        <div style={{ fontSize: tokens.FontSizeSmall, color: tokens.ColorTextSecondary }}>
          <p>Font Family: {tokens.FontFamilyPrimary}</p>
          <p>Display Size: {tokens.FontSizeDisplay}px</p>
          <p>H1 Size: {tokens.FontSizeH1}px</p>
          <p>H2 Size: {tokens.FontSizeH2}px</p>
          <p>Body Size: {tokens.FontSizeBody}px</p>
          <p>Caption Size: {tokens.FontSizeCaption}px</p>
          <p>Small Size: {tokens.FontSizeSmall}px</p>
          <p>Regular Weight: {tokens.FontWeightRegular}</p>
          <p>Medium Weight: {tokens.FontWeightMedium}</p>
          <p>Semibold Weight: {tokens.FontWeightSemibold}</p>
          <p>Bold Weight: {tokens.FontWeightBold}</p>
          <p>Display Line Height: {tokens.FontLineheightDisplay}</p>
          <p>Heading Line Height: {tokens.FontLineheightHeading}</p>
          <p>Body Line Height: {tokens.FontLineheightBody}</p>
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <Typography variant="display" weight="bold">
          Display
        </Typography>
        <Typography variant="h1" weight="bold">
          Heading 1
        </Typography>
        <Typography variant="h2" weight="semibold">
          Heading 2
        </Typography>
        <Typography variant="body" weight="regular">
          Body Text
        </Typography>
        <Typography variant="caption" weight="regular">
          Caption Text
        </Typography>
        <Typography variant="small" weight="regular">
          Small Text
        </Typography>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'This story showcases the actual design token values used in the typography component.',
      },
    },
  },
};
