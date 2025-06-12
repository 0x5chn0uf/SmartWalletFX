/// <reference types="cypress" />

const VALID_ADDRESS = '0x1234123412341234123412341234123412341234';

describe('Timeline Chart', () => {
  beforeEach(() => {
    cy.intercept('GET', /\/defi\/timeline\//, {
      statusCode: 200,
      body: require('../fixtures/timelineSnapshots.json'),
    }).as('getTimeline');
  });

  it('renders TimelineChart after fetching snapshots', () => {
    cy.visit('/');

    // Type a valid address to enable fetching
    cy.get('input[label="Wallet Address"], input[placeholder="Wallet Address"], input')
      .first()
      .clear()
      .type(VALID_ADDRESS);

    // Wait for timeline API call to complete
    cy.wait('@getTimeline');

    // Ensure the chart SVG renders (Recharts uses <svg>)
    cy.get('svg').should('exist');

    // Check that at least one line path is drawn
    cy.get('svg path').its('length').should('be.gte', 1);
  });
}); 