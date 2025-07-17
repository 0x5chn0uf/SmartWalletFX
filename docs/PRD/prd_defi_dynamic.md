# Portfolio Dashboard PRD

## Overview

Currently, the portfolio dashboard page shows static mock data and is accessed through a fixed route `/defi`. This PRD outlines the requirements for making the portfolio dashboard dynamic based on wallet addresses, with a focus on converting visitors to registered users.

## Current State

- Fixed `/defi` route shows mock data
- No connection to real wallet addresses
- Static performance metrics and charts
- No personalized data
- Full feature access without registration

## Goals

1. Enable wallet-specific portfolio views
2. Convert visitors to registered users
3. Maintain consistent UX across the application
4. Support deep linking to specific wallet's positions
5. Create clear value proposition for registration

## Requirements

### 1. Routing Updates

- Change route from `/defi` to `/portfolio/:address` to support wallet-specific views
- Handle invalid wallet addresses gracefully
- Redirect old `/defi` routes to `/portfolio`

### 2. Homepage Integration

- Use the wallet address input field in the homepage's hero section
- Implement real-time validation of wallet address format
- Add a "View Portfolio" button that redirects to `/portfolio/:address`
- Clear call-to-action for registration benefits

### 3. Navigation

- Simplify navigation bar for non-registered users:
  - Option 1: Show only "Portfolio" tab
  - Option 2: Hide navigation completely for cleaner preview experience
  - Add prominent "Sign Up" button in header
- Full navigation only visible to registered users

### 4. Limited Preview Features - Propositions

#### Proposition 1: Time-Based Preview

##### Non-Registered Users Can Access:

- Last 24 hours of portfolio data
- Current TVL and basic position list
- Simple price charts (24h only)
- Basic portfolio breakdown

##### Registration Wall Triggers:

- Attempting to view historical data beyond 24h
- "View Complete History" buttons on all charts
- Tooltip: "Register to unlock your complete portfolio history"
- Preview of 7d/30d charts (blurred with overlay)

#### Proposition 2: Depth-Based Preview

##### Non-Registered Users Can Access:

- Top 3 largest positions only
- Basic portfolio total value
- Simple protocol distribution chart
- Current APY for visible positions

Preview Dashboard Features:

1. Token Tracking Overview
   Free Preview:
   - Top 3 tokens by value in the wallet
     - Current token price
     - 24h price change (%)
     - Basic token information (name, symbol, network)
     - Simple price chart (24h)
     - Current balance and USD value

   Premium Features (Blurred/Locked):
   - Complete token list (showing "X more tokens hidden")
   - Historical balance changes
   - Token transfer history
   - Price alerts setup
   - Custom token grouping
   - Multi-chain token view

2. Portfolio Performance Snapshot
   Free Preview:
   - 24h performance for top 3 tokens
     - Total value change in USD and percentage
     - Color-coded indicators (green/red)
     - Simple sparkline showing 24h trend
     - Basic balance changes

   Premium Features (Blurred/Locked):
   - Complete portfolio analysis
     - Historical performance tracking
     - Custom date range analysis
     - Token correlation insights
     - Portfolio diversification score
     - Price movement alerts
     - Export functionality
     - Tax reporting tools

   Interactive Elements:
   - Hoverable tooltips with "Unlock" prompts
   - Blurred premium charts preview
   - One-click registration buttons
   - Sample premium feature demos

##### Registration Wall Triggers:

- "X more positions hidden" counter
- Blurred preview of remaining positions
- "Unlock Full Portfolio" overlay on hidden positions
- Preview of detailed metrics (shown but locked)

#### Proposition 3: Feature-Based Preview

##### Non-Registered Users Can Access:

- Read-only portfolio overview
- Single protocol detailed view
- Basic performance metrics
- Simple position list

##### Registration Wall Triggers:

- Multi-protocol comparison features locked
- Analytics features shown but disabled
- Export functionality visible but locked
- Custom labeling and notes features previewed

### 5. Recommended Approach

Based on user psychology and market research, we recommend implementing **Proposition 2: Depth-Based Preview** because:

- Creates immediate curiosity about hidden positions
- Provides tangible value while clearly showing limitations
- Easy to understand value proposition ("see all your positions")
- Natural progression from preview to full access
- Strong visual incentive to register

### 5. UI Design Specifications

#### Layout Structure

1. Header Section
   - Clean, minimal navigation (Portfolio tab only)
   - Wallet address display with copy button
   - Prominent "Sign Up" button with contrasting color
   - Optional: ENS name display if available

2. Main Dashboard Grid

   ```
   [Total Portfolio Value]  [24h Change]
   [Token List Preview]    [Performance Chart]
   [Premium Features]      [Registration CTA]
   ```

3. Token List Preview Card
   - Prominent card with depth effect
   - Top 3 tokens displayed in order of value
   - Each token row:
     ```
     [Token Icon] [Name] [Price] [24h Change] [Balance]
     ```
   - Bottom section with blurred additional tokens
   - "X more tokens" overlay with unlock button

4. Performance Chart Card
   - 24h price chart for visible tokens
   - Clean, minimal design
   - Blurred extended timeframe options
   - "Unlock Full History" overlay on hover

#### Visual Hierarchy

1. Primary Elements (Most Visible)
   - Total portfolio value
   - Top 3 token listings
   - 24h performance metrics
   - Registration CTAs

2. Secondary Elements
   - Token details
   - Basic charts
   - Copy/share buttons
   - Navigation elements

3. Tertiary Elements (Subtle)
   - Tooltips
   - Helper text
   - Additional information

#### Interactive Elements

1. Token Preview Interactions
   - Hover effects on token rows
   - Click to expand basic token info
   - Smooth transitions for price updates
   - Blurred premium features with hover effects

2. Registration Triggers
   - Floating "Unlock" button follows scroll
   - Subtle animation on CTA buttons
   - Modal previews of premium features
   - One-click registration flow

#### Color System

1. Base Theme
   - Primary: #4fd1c7 (Brand teal)
   - Secondary: #6366f1 (Interactive elements)
   - Background: #1a1f2e (Dark mode)
   - Text: #e0e7ef (Light text)

2. Status Colors
   - Positive: #10b981 (Green)
   - Negative: #ef4444 (Red)
   - Warning: #f59e0b (Orange)
   - Info: #3b82f6 (Blue)

3. Premium Feature Indication
   - Gradient overlay: linear-gradient(135deg, #4fd1c7 0%, #6366f1 100%)
   - Blur effect: backdrop-filter: blur(4px)
   - Premium badge: #ffd700 (Gold)

#### Typography

1. Hierarchy
   - Headers: Inter 24px/700
   - Subheaders: Inter 18px/600
   - Body: Inter 14px/400
   - Metrics: Inter 16px/500
   - CTAs: Inter 16px/600

2. Special Elements
   - Token amounts: Monospace font
   - Percentage changes: Semi-bold weight
   - Premium labels: All caps, letter-spacing: 0.05em

#### Responsive Behavior

1. Desktop (>1200px)
   - Full two-column layout
   - Expanded token information
   - Side-by-side charts

2. Tablet (768px - 1199px)
   - Stack cards vertically
   - Maintain token list width
   - Condensed chart view

3. Mobile (<767px)
   - Single column layout
   - Collapsible token details
   - Simplified charts
   - Fixed CTA button at bottom

#### Animation Guidelines

1. State Changes
   - Price updates: Subtle highlight fade
   - Loading states: Shimmer effect
   - Error states: Gentle shake

2. Premium Feature Preview
   - Hover: Scale transform (1.02)
   - Blur transition: 200ms ease
   - CTA pulse: Subtle glow effect

3. Registration Flow
   - Modal entrance: Fade up + scale
   - Success confirmation: Checkmark animation
   - Error feedback: Gentle bounce

#### Accessibility Considerations

1. Color Contrast
   - All text meets WCAG AA standards
   - Alternative indicators beyond color
   - Clear focus states

2. Interactive Elements
   - Minimum touch target size: 44px
   - Keyboard navigation support
   - Screen reader optimized

3. Loading States
   - Clear loading indicators
   - Maintain layout stability
   - Fallback content

### 6. Registration Prompts

- Implement non-intrusive but visible registration CTAs:
  - Overlay on locked features
  - "Unlock full access" buttons
  - Feature comparison tooltips
  - Limited historical data with "View More" prompts
- Show clear value proposition for registration
- Easy one-click registration process

### 6. Data Integration

- Implement preview data fetching with rate limiting
- Add proper loading states
- Handle error states appropriately
- Clear indication of preview mode

### 7. UI/UX Requirements

- Add wallet address display in the portfolio dashboard header
- Show "Preview Mode" indicator for non-registered users
- Implement clear visual hierarchy between available and locked features
- Add registration CTAs in strategic locations
- Show wallet ENS name if available
- Implement error states for:
  - Invalid addresses
  - Network errors
  - No data available

### 8. Technical Requirements

- Update frontend routing configuration
- Implement feature-gating based on authentication
- Add new API endpoints with rate limiting
- Handle wallet address validation
- Support both checksummed and non-checksummed addresses

## API Requirements

### New/Updated Endpoints

1. `/portfolio/:address/preview`
   - Returns limited metrics for non-registered users
2. `/portfolio/:address/overview`
   - Returns full metrics for registered users
3. `/portfolio/:address/positions`
   - Returns detailed position breakdown (limited for non-registered)
4. `/portfolio/:address/history`
   - Returns historical data (limited timeframe for non-registered)

### Response Formats

```typescript
interface PortfolioPreview {
  address: string;
  ensName?: string;
  totalValue: number;
  totalValueChange24h: number;
  basicPositions: BasicPosition[];
  previewFeatures: LockedFeature[];
}

interface FullPortfolioData extends PortfolioPreview {
  historicalData: HistoricalData[];
  detailedMetrics: DetailedMetrics;
  protocolBreakdown: ProtocolData[];
  // ... additional premium features
}

interface LockedFeature {
  id: string;
  name: string;
  description: string;
  previewImage?: string;
}
```

## Success Metrics

1. Conversion rate:
   - Preview to registration rate
   - Time to registration
   - Feature-specific conversion triggers
2. User engagement:
   - Time spent on preview
   - Interaction with locked features
   - Registration CTA click-through rate
3. Performance:
   - Page load time < 2s
   - API response time < 500ms
4. Error rates:
   - Invalid wallet address attempts
   - Failed API calls
   - Error page displays

## Implementation Phases

### Phase 1: Core Preview Experience

- Update routing and navigation
- Implement basic preview functionality
- Add registration CTAs
- Basic feature gating

### Phase 2: Enhanced Preview

- Improve registration flow
- Add feature previews
- Implement "locked feature" UI
- Add ENS support

### Phase 3: Premium Features

- Implement full feature set for registered users
- Add advanced analytics
- Real-time updates
- Mobile optimizations

## Future Considerations

1. A/B testing different preview limitations
2. Dynamic feature gating based on user behavior
3. Referral program for registered users
4. Premium tier features
5. Integration with additional protocols
6. Advanced portfolio analytics
