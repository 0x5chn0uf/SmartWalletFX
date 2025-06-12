/// <reference types="cypress" />

describe('Home page', () => {
  it('loads and displays title', () => {
    cy.visit('/');
    cy.contains('SmartWalletFX');
  });
}); 