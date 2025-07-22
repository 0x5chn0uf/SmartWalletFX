import React, { Component, ErrorInfo, ReactNode } from 'react';
import styled from '@emotion/styled';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

const ErrorContainer = styled.div`
  padding: 2rem;
  text-align: center;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: #fef2f2;
`;

const ErrorTitle = styled.h2`
  color: #dc2626;
  font-size: 1.5rem;
  margin-bottom: 1rem;
`;

const ErrorMessage = styled.p`
  color: #6b7280;
  margin-bottom: 2rem;
  max-width: 500px;
`;

const ErrorDetails = styled.details`
  margin: 1rem 0;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  text-align: left;
  max-width: 600px;

  summary {
    cursor: pointer;
    font-weight: 600;
    color: #374151;
  }
`;

const ErrorCode = styled.pre`
  background: #f3f4f6;
  padding: 1rem;
  border-radius: 0.375rem;
  overflow-x: auto;
  font-size: 0.875rem;
  color: #1f2937;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  justify-content: center;
`;

const Button = styled.button<{ variant?: 'primary' | 'secondary' }>`
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid;

  ${props =>
    props.variant === 'primary'
      ? `
    background: #3b82f6;
    color: white;
    border-color: #3b82f6;
    
    &:hover {
      background: #2563eb;
      border-color: #2563eb;
    }
  `
      : `
    background: transparent;
    color: #6b7280;
    border-color: #d1d5db;
    
    &:hover {
      background: #f9fafb;
    }
  `}
`;

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Enhanced logging with more context
    console.error('ErrorBoundary caught an error:', {
      error,
      errorInfo,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    });

    // Store error info for display in development
    this.setState({ errorInfo });

    // In production, you might want to send this to an error reporting service
    if (process.env.NODE_ENV === 'production') {
      // Example: Send to error reporting service
      // errorReportingService.report(error, errorInfo);
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const isDevelopment = process.env.NODE_ENV === 'development';

      return (
        <ErrorContainer>
          <ErrorTitle>Oops! Something went wrong</ErrorTitle>
          <ErrorMessage>
            We're sorry, but something unexpected happened. You can try to recover by resetting the
            component or reloading the page.
          </ErrorMessage>

          {isDevelopment && this.state.error && (
            <ErrorDetails>
              <summary>Error Details (Development)</summary>
              <ErrorCode>
                {this.state.error.toString()}
                {this.state.errorInfo?.componentStack}
              </ErrorCode>
            </ErrorDetails>
          )}

          <ButtonGroup>
            <Button variant="primary" onClick={this.handleReset}>
              Try Again
            </Button>
            <Button variant="secondary" onClick={() => window.location.reload()}>
              Reload Page
            </Button>
          </ButtonGroup>
        </ErrorContainer>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
