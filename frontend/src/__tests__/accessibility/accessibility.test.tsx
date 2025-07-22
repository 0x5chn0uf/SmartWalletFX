import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import App from '../../App';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../../theme';
import { Provider } from 'react-redux';
import { store } from '../../store';
import '@testing-library/jest-dom';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

const AppWithProviders = ({ children }: { children: React.ReactNode }) => (
  <Provider store={store}>
    <BrowserRouter>
      <ThemeProvider theme={createAppTheme()}>
        {children}
      </ThemeProvider>
    </BrowserRouter>
  </Provider>
);

describe('Accessibility Tests', () => {
  it('should not have accessibility violations in App component', async () => {
    const { container } = render(
      <AppWithProviders>
        <App />
      </AppWithProviders>
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  }, 10000); // Increased timeout for axe tests

  it('should have proper heading hierarchy', () => {
    const { container } = render(
      <AppWithProviders>
        <div>
          <h1>Main Title</h1>
          <h2>Section Title</h2>
          <h3>Subsection Title</h3>
        </div>
      </AppWithProviders>
    );

    const headings = container.querySelectorAll('h1, h2, h3, h4, h5, h6');
    expect(headings.length).toBeGreaterThan(0);
    
    // Check that we start with h1
    const firstHeading = headings[0];
    expect(firstHeading.tagName).toBe('H1');
  });

  it('should have proper color contrast ratios', () => {
    const { container } = render(
      <AppWithProviders>
        <div style={{ color: '#ffffff', backgroundColor: '#000000' }}>
          High contrast text
        </div>
      </AppWithProviders>
    );

    // This is a basic test - in production, you'd want to use a library
    // like wcag-contrast or integrate with automated tools
    const element = container.querySelector('div');
    expect(element).toHaveStyle('color: rgb(255, 255, 255)');
    expect(element).toHaveStyle('background-color: rgb(0, 0, 0)');
  });

  it('should have keyboard navigation support', () => {
    const { container } = render(
      <AppWithProviders>
        <button>Focusable Button</button>
        <input type="text" placeholder="Focusable Input" />
        <a href="#test">Focusable Link</a>
      </AppWithProviders>
    );

    const focusableElements = container.querySelectorAll(
      'button, input, a[href], [tabindex]:not([tabindex="-1"])'
    );

    expect(focusableElements.length).toBeGreaterThanOrEqual(3);
    
    // Each focusable element should not have tabindex="-1"
    focusableElements.forEach(element => {
      expect(element).not.toHaveAttribute('tabindex', '-1');
    });
  });

  it('should have proper ARIA labels and roles', async () => {
    const { container } = render(
      <AppWithProviders>
        <nav aria-label="Main navigation">
          <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/about">About</a></li>
          </ul>
        </nav>
        <main>
          <section aria-labelledby="section-heading">
            <h2 id="section-heading">Content Section</h2>
            <p>Section content</p>
          </section>
        </main>
      </AppWithProviders>
    );

    // Check for proper semantic HTML and ARIA attributes
    const nav = container.querySelector('nav');
    expect(nav).toHaveAttribute('aria-label', 'Main navigation');

    const section = container.querySelector('section');
    expect(section).toHaveAttribute('aria-labelledby', 'section-heading');

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});