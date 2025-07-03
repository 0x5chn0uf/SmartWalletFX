import React from 'react';
import { render, screen } from '@testing-library/react';
import { Layout } from '../../../../components/Layout/Layout';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../../../../theme';

describe('Layout Component', () => {
  const theme = createAppTheme();

  const renderWithTheme = (component: React.ReactNode) => {
    return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
  };

  it('should render children content', () => {
    const testContent = 'Test Content';
    renderWithTheme(
      <Layout>
        <div>{testContent}</div>
      </Layout>
    );

    expect(screen.getByText(testContent)).toBeInTheDocument();
  });

  it('should apply correct styles to Box component', () => {
    const { container } = renderWithTheme(
      <Layout>
        <div>Content</div>
      </Layout>
    );

    const box = container.querySelector('.MuiBox-root');
    expect(box).toBeInTheDocument();
    expect(box).toHaveStyle({
      minHeight: '100vh',
      backgroundColor: theme.palette.background.default,
    });
  });

  it('should render Container with correct maxWidth', () => {
    const { container } = renderWithTheme(
      <Layout>
        <div>Content</div>
      </Layout>
    );

    const containerElement = container.querySelector('.MuiContainer-root');
    expect(containerElement).toBeInTheDocument();
    expect(containerElement).toHaveClass('MuiContainer-maxWidthXl');
  });

  it('should include CssBaseline component', () => {
    const { container } = renderWithTheme(
      <Layout>
        <div>Content</div>
      </Layout>
    );

    // CssBaseline injects styles into the document head
    const cssBaseline = document.querySelector('style[data-emotion]');
    expect(cssBaseline).toBeInTheDocument();
  });
});
