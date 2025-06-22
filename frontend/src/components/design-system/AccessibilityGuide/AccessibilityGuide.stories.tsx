import type { Meta, StoryObj } from '@storybook/react';
import { Box, Typography, Paper, List, ListItem, ListItemText } from '@mui/material';

const meta: Meta = {
  title: 'Design System/Accessibility Guide',
  parameters: {
    docs: {
      description: {
        component:
          'Guidelines and best practices for creating accessible components in our design system.',
      },
    },
  },
};

export default meta;
type Story = StoryObj;

export const Overview: Story = {
  render: () => (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h3" gutterBottom>
        Accessibility Guidelines
      </Typography>

      <Typography variant="body1" paragraph>
        All components in our design system must meet WCAG 2.1 AA standards. This guide provides
        essential patterns and best practices for creating accessible components.
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Color Contrast Requirements
        </Typography>
        <List>
          <ListItem>
            <ListItemText primary="Normal text" secondary="Minimum 4.5:1 contrast ratio" />
          </ListItem>
          <ListItem>
            <ListItemText
              primary="Large text (18pt+ or 14pt+ bold)"
              secondary="Minimum 3:1 contrast ratio"
            />
          </ListItem>
          <ListItem>
            <ListItemText
              primary="Muted/decorative text"
              secondary="Minimum 2.5:1 contrast ratio"
            />
          </ListItem>
          <ListItem>
            <ListItemText
              primary="UI components and graphics"
              secondary="Minimum 3:1 contrast ratio"
            />
          </ListItem>
        </List>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Keyboard Navigation
        </Typography>
        <List>
          <ListItem>
            <ListItemText primary="Tab order" secondary="Logical, intuitive tab sequence" />
          </ListItem>
          <ListItem>
            <ListItemText
              primary="Focus indicators"
              secondary="Visible focus states for all interactive elements"
            />
          </ListItem>
          <ListItem>
            <ListItemText
              primary="Skip links"
              secondary="Skip to main content links where appropriate"
            />
          </ListItem>
          <ListItem>
            <ListItemText primary="Keyboard shortcuts" secondary="No keyboard traps" />
          </ListItem>
        </List>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Screen Reader Support
        </Typography>
        <List>
          <ListItem>
            <ListItemText primary="Semantic HTML" secondary="Proper heading hierarchy (h1-h6)" />
          </ListItem>
          <ListItem>
            <ListItemText
              primary="ARIA labels"
              secondary="Descriptive labels for interactive elements"
            />
          </ListItem>
          <ListItem>
            <ListItemText primary="Alt text" secondary="Meaningful alternative text for images" />
          </ListItem>
          <ListItem>
            <ListItemText primary="Landmarks" secondary="Proper use of ARIA landmarks" />
          </ListItem>
        </List>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          Development Checklist
        </Typography>
        <List>
          <ListItem>
            <ListItemText
              primary="✓ Use design tokens for colors"
              secondary="Ensures consistent contrast ratios"
            />
          </ListItem>
          <ListItem>
            <ListItemText
              primary="✓ Test in Storybook with a11y addon"
              secondary="Automated accessibility testing"
            />
          </ListItem>
          <ListItem>
            <ListItemText
              primary="✓ Verify keyboard navigation"
              secondary="Tab through all interactive elements"
            />
          </ListItem>
          <ListItem>
            <ListItemText
              primary="✓ Add ARIA attributes where needed"
              secondary="Enhance screen reader experience"
            />
          </ListItem>
          <ListItem>
            <ListItemText primary="✓ Test with screen readers" secondary="NVDA, JAWS, VoiceOver" />
          </ListItem>
        </List>
      </Paper>
    </Box>
  ),
};

export const CodeExamples: Story = {
  render: () => (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h3" gutterBottom>
        Accessibility Code Examples
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Button Components
        </Typography>
        <Typography
          variant="body2"
          component="pre"
          sx={{
            backgroundColor: 'grey.100',
            p: 2,
            borderRadius: 1,
            overflow: 'auto',
          }}
        >
          {`// Good: Proper ARIA and keyboard support
<Button
  aria-label="Close dialog"
  onClick={handleClose}
  onKeyDown={(e) => e.key === 'Escape' && handleClose()}
>
  Close
</Button>`}
        </Typography>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Form Controls
        </Typography>
        <Typography
          variant="body2"
          component="pre"
          sx={{
            backgroundColor: 'grey.100',
            p: 2,
            borderRadius: 1,
            overflow: 'auto',
          }}
        >
          {`// Good: Proper labeling and error handling
<TextField
  label="Email Address"
  aria-describedby="email-error"
  error={!!emailError}
  helperText={emailError}
  id="email-error"
/>`}
        </Typography>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          Navigation Components
        </Typography>
        <Typography
          variant="body2"
          component="pre"
          sx={{
            backgroundColor: 'grey.100',
            p: 2,
            borderRadius: 1,
            overflow: 'auto',
          }}
        >
          {`// Good: Semantic navigation with ARIA
<nav aria-label="Main navigation">
  <ul role="menubar">
    <li role="none">
      <a role="menuitem" href="/dashboard">
        Dashboard
      </a>
    </li>
  </ul>
</nav>`}
        </Typography>
      </Paper>
    </Box>
  ),
};
