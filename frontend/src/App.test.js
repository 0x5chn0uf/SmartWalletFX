import { render, screen } from '@testing-library/react';
import App from './App';
import { ThemeProvider } from './providers/ThemeProvider';

test('renders navigation links', () => {
  render(
    <ThemeProvider>
      <App />
    </ThemeProvider>,
  );
  const linkElement = screen.getByText(/Home/i);
  expect(linkElement).toBeInTheDocument();
});
