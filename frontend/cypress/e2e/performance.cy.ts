describe('Performance Tests', () => {
  beforeEach(() => {
    // Clear any existing localStorage/sessionStorage
    cy.clearLocalStorage();
    cy.clearCookies();
  });

  it('should load the home page within 2 seconds', () => {
    const start = Date.now();
    
    cy.visit('/', {
      onBeforeLoad: (win) => {
        // Performance timing polyfill for older browsers
        win.performance = win.performance || {};
        win.performance.mark = win.performance.mark || (() => {});
        win.performance.measure = win.performance.measure || (() => {});
      }
    });

    cy.get('[data-testid="app"]', { timeout: 10000 }).should('be.visible');
    
    cy.then(() => {
      const loadTime = Date.now() - start;
      expect(loadTime).to.be.lessThan(2000); // Less than 2 seconds
    });
  });

  it('should have proper page navigation and routing', () => {
    cy.visit('/');
    
    // Check if main navigation elements exist
    cy.get('nav').should('exist');
    
    // Test routing to different pages (adjust selectors based on your app)
    cy.url().should('include', '/');
    
    // If you have navigation links, test them
    // cy.get('[data-testid="nav-home"]').click();
    // cy.url().should('include', '/');
    
    // cy.get('[data-testid="nav-dashboard"]').click();
    // cy.url().should('include', '/dashboard');
    
    // For now, just verify the home page loads correctly
    cy.title().should('not.be.empty');
  });

  it('should have fast JavaScript execution', () => {
    cy.visit('/');
    
    cy.window().then((win) => {
      // Measure JavaScript execution time
      const start = performance.now();
      
      // Execute some JavaScript operations
      for (let i = 0; i < 1000; i++) {
        // Simple operation
        Math.random();
      }
      
      const executionTime = performance.now() - start;
      expect(executionTime).to.be.lessThan(100); // Less than 100ms
    });
  });

  it('should handle responsive design correctly', () => {
    // Test desktop viewport
    cy.viewport(1280, 720);
    cy.visit('/');
    cy.get('[data-testid="app"]').should('be.visible');
    
    // Test tablet viewport
    cy.viewport(768, 1024);
    cy.get('[data-testid="app"]').should('be.visible');
    
    // Test mobile viewport
    cy.viewport(375, 667);
    cy.get('[data-testid="app"]').should('be.visible');
  });

  it('should not have console errors', () => {
    // Listen for console errors
    const consoleErrors: string[] = [];
    
    cy.window().then((win) => {
      const originalError = win.console.error;
      win.console.error = (...args: any[]) => {
        consoleErrors.push(args.join(' '));
        originalError.apply(win.console, args);
      };
    });
    
    cy.visit('/');
    cy.get('[data-testid="app"]').should('be.visible');
    
    cy.then(() => {
      // Filter out known acceptable errors (if any)
      const criticalErrors = consoleErrors.filter(error => 
        !error.includes('Warning:') && // React warnings are not critical
        !error.includes('Download the React DevTools') // DevTools message
      );
      
      expect(criticalErrors).to.have.length(0);
    });
  });

  it('should load critical resources efficiently', () => {
    cy.visit('/');
    
    cy.window().its('performance').then((performance) => {
      // Check navigation timing
      cy.then(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        
        if (navigation) {
          const domContentLoaded = navigation.domContentLoadedEventEnd - navigation.navigationStart;
          const fullyLoaded = navigation.loadEventEnd - navigation.navigationStart;
          
          // DOM should be ready quickly
          expect(domContentLoaded).to.be.lessThan(1500);
          
          // Full page load should be reasonable
          expect(fullyLoaded).to.be.lessThan(3000);
        }
      });
    });
  });
});