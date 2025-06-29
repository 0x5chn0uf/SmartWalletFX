import React from 'react';
import styled from '@emotion/styled';
import { keyframes } from '@emotion/react';
import { Link as RouterLink } from 'react-router-dom';
import { FiLink, FiBarChart2, FiZap } from 'react-icons/fi';

const fadeIn = keyframes`
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const heroGlowPulse = keyframes`
  0% {
    opacity: 0.7;
    filter: blur(32px);
  }
  100% {
    opacity: 1;
    filter: blur(60px);
  }
`;

const Container = styled.div`
  min-height: 100vh;
  background: #1a1f2e;
  color: #e0e7ef;
  display: flex;
  flex-direction: column;
`;

const Header = styled.header`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  background: rgba(26, 31, 46, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  position: sticky;
  top: 0;
  z-index: 10;
  animation: ${fadeIn} 0.5s ease-out;

  @media (max-width: 768px) {
    padding: 16px;
    flex-direction: column;
    gap: 16px;
  }
`;

const Logo = styled(RouterLink)`
  color: #4fd1c7;
  text-decoration: none;
  font-weight: 800;
  font-size: 24px;
  letter-spacing: -0.02em;
  text-shadow: 0 2px 8px rgba(79, 209, 199, 0.2);
`;

const Nav = styled.nav`
  display: flex;
  gap: 32px;
  align-items: center;
`;

const NavLink = styled.a`
  color: #9ca3af;
  text-decoration: none;
  font-weight: 600;
  font-size: 16px;
  transition: color 0.2s;
  cursor: pointer;

  &:hover {
    color: #4fd1c7;
  }
`;

const LoginLink = styled(RouterLink)`
  color: #9ca3af;
  text-decoration: none;
  font-weight: 600;
  font-size: 16px;
  transition: color 0.2s;

  &:hover {
    color: #4fd1c7;
  }
`;

const HeroHalo = styled.div`
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 80vw;
  height: 60vh;
  background: radial-gradient(
    circle,
    rgba(79, 209, 199, 0.25) 0%,
    rgba(99, 102, 241, 0.18) 60%,
    transparent 100%
  );
  filter: blur(40px);
  z-index: -1;
  pointer-events: none;
  animation: ${heroGlowPulse} 4s ease-in-out infinite alternate;
`;

const HeroSection = styled.section`
  text-align: center;
  padding: 100px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  animation: ${fadeIn} 0.8s ease-out;
  position: relative;
  overflow: visible;
  z-index: 0;

  & > *:not(${/* sc-selector for HeroHalo */ 'div'}) {
    position: relative;
    z-index: 1;
  }
`;

const HeroTitle = styled.h1`
  font-size: clamp(40px, 8vw, 64px);
  font-weight: 800;
  margin-bottom: 16px;
  line-height: 1.1;
  letter-spacing: -0.02em;
  max-width: 800px;
  color: #fff;
`;

const HeroSubtitle = styled.p`
  color: #9ca3af;
  font-size: 18px;
  margin-bottom: 32px;
  max-width: 600px;
  line-height: 1.6;
`;

const CallToActionButton = styled(RouterLink)`
  background: linear-gradient(90deg, #4fd1c7 0%, #6366f1 100%);
  color: #1f2937;
  border: none;
  border-radius: 10px;
  padding: 14px 32px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  text-decoration: none;
  box-shadow: 0 2px 8px rgba(79, 209, 199, 0.15);
  transition:
    transform 0.18s,
    box-shadow 0.18s;

  &:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.18);
  }
`;

const FeaturesSection = styled.section`
  padding: 80px 24px;
  background: #151a28;
`;

const FeaturesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin: 0 auto;
`;

const FeatureCard = styled.div`
  background: rgba(36, 41, 55, 0.5);
  padding: 16px 32px;
  border-radius: 16px;
  border: 1.5px solid rgba(255, 255, 255, 0.08);
  text-align: center;
  transition:
    transform 0.2s,
    border-color 0.2s;
  animation: ${fadeIn} 1s ease-out;

  &:hover {
    transform: translateY(-5px);
    border-color: #4fd1c7;
  }
`;

const FeatureTitle = styled.h3`
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 12px;
  color: #fff;
`;

const FeatureDescription = styled.p`
  color: #9ca3af;
  font-size: 16px;
  line-height: 1.6;
`;

const Footer = styled.footer`
  text-align: center;
  padding: 24px;
  background: #151a28;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
`;

const FooterText = styled.p`
  color: #7b879d;
  font-size: 14px;
`;

const FEATURES = [
  { title: 'Unified Dashboard', description: 'View all your investments in one place.' },
  { title: 'Performance Metrics', description: 'Get detailed insights and performance summaries.' },
  {
    title: 'Alerts & Notifications',
    description: 'Stay informed with custom price and portfolio alerts.',
  },
  { title: 'Secure Sync', description: 'Protect your data with industry-standard encryption.' },
];

// Quick Product Preview Section Styles
const QuickPreviewSection = styled.section`
  max-width: 500px;
  margin: 40px auto 0;
  padding: 0 0 24px 0;
`;

// Animation for steps
const stepFadeInUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(32px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const QuickPreviewTitle = styled.h2`
  text-align: center;
  font-size: 2.2rem;
  font-weight: 900;
  margin-bottom: 36px;
  background: linear-gradient(90deg, #4fd1c7 0%, #6366f1 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-fill-color: transparent;
  letter-spacing: -0.01em;
  text-shadow: 0 2px 12px rgba(79, 209, 199, 0.1);
`;

// Refactored ProgressBarWrapper and ProgressStep for perfect alignment
const ProgressBarWrapper = styled.div`
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  position: relative;
  gap: 0;
  min-height: 220px;
  margin: 0 auto;
`;
const ProgressBarLine = styled.div`
  position: absolute;
  left: 20px;
  top: 32px;
  width: 3px;
  height: calc(100% - 64px);
  background: linear-gradient(to bottom, #4fd1c7 0%, #6366f1 60%, #ffd600 100%);
  z-index: 0;
`;
const StepText = styled.div`
  display: flex;
  flex-direction: column;
`;
const StepDetails = styled.div`
  opacity: 0;
  max-height: 0;
  overflow: hidden;
  color: #9ca3af;
  font-size: 0.9rem;
  margin-top: 4px;
  transition:
    opacity 0.25s ease,
    max-height 0.25s ease;
`;
const ProgressStep = styled.div<{ color: string; delay: number }>`
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-bottom: 24px;
  position: relative;
  z-index: 1;
  opacity: 0;
  animation: ${stepFadeInUp} 0.7s cubic-bezier(0.4, 0, 0.2, 1) forwards;
  animation-delay: ${({ delay }) => delay}s;
  &:last-child {
    margin-bottom: 0;
  }
  &:hover .step-details {
    opacity: 1;
    max-height: 120px;
  }
`;
const StepCircle = styled.div<{ color: string }>`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #23273a;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
  color: ${({ color }) => color};
  border: 2px solid ${({ color }) => color};
  z-index: 2;
`;
const StepContent = styled.div`
  display: flex;
  align-items: center;
  gap: 14px;
  margin-left: 24px;
`;
const StepLabel = styled.div`
  font-size: 1.1rem;
  font-weight: 600;
`;
const StepIcon = styled.div<{ color: string }>`
  font-size: 2rem;
  color: ${({ color }) => color};
`;

const LandingPage: React.FC = () => {
  return (
    <Container>
      <Header>
        <Logo to="/">SmartWalletFX</Logo>
        <Nav>
          <NavLink href="#features">Features</NavLink>
          <NavLink href="#pricing">Pricing</NavLink>
          <LoginLink to="/login-register">Login</LoginLink>
        </Nav>
      </Header>

      <main>
        <HeroSection>
          <HeroHalo />
          <HeroTitle>Track. Analyze. Grow.</HeroTitle>
          <HeroSubtitle>
            All-in-one portfolio management for crypto and traditional assets.
          </HeroSubtitle>
          <CallToActionButton to="/login-register">Start Tracking</CallToActionButton>
        </HeroSection>

        <FeaturesSection id="features">
          <FeaturesGrid>
            {FEATURES.map(feature => (
              <FeatureCard key={feature.title}>
                <FeatureTitle>{feature.title}</FeatureTitle>
                <FeatureDescription>{feature.description}</FeatureDescription>
              </FeatureCard>
            ))}
          </FeaturesGrid>
        </FeaturesSection>

        {/* Quick Product Preview Section */}
        <QuickPreviewSection>
          <QuickPreviewTitle>Quick Product Preview</QuickPreviewTitle>
          <ProgressBarWrapper>
            <ProgressBarLine />
            <ProgressStep color="#4fd1c7" delay={0.1}>
              <StepCircle color="#4fd1c7">1</StepCircle>
              <StepContent>
                <StepIcon color="#4fd1c7">
                  <FiLink />
                </StepIcon>
                <StepText>
                  <StepLabel>Retrieve Wallet</StepLabel>
                  <StepDetails className="step-details">
                    Connect your wallet or paste address to import transactions.
                  </StepDetails>
                </StepText>
              </StepContent>
            </ProgressStep>
            <ProgressStep color="#6366f1" delay={0.35}>
              <StepCircle color="#6366f1">2</StepCircle>
              <StepContent>
                <StepIcon color="#6366f1">
                  <FiBarChart2 />
                </StepIcon>
                <StepText>
                  <StepLabel>Analyze PnL & Metrics</StepLabel>
                  <StepDetails className="step-details">
                    Gain insights into performance, ROI and detailed metrics.
                  </StepDetails>
                </StepText>
              </StepContent>
            </ProgressStep>
            <ProgressStep color="#ffd600" delay={0.6}>
              <StepCircle color="#ffd600">3</StepCircle>
              <StepContent>
                <StepIcon color="#ffd600">
                  <FiZap />
                </StepIcon>
                <StepText>
                  <StepLabel>See What Smart Money Is Doing</StepLabel>
                  <StepDetails className="step-details">
                    Discover trends and follow top performing wallets.
                  </StepDetails>
                </StepText>
              </StepContent>
            </ProgressStep>
          </ProgressBarWrapper>
        </QuickPreviewSection>
      </main>

      <Footer>
        <FooterText>© 2025 SmartWalletFX. All rights reserved.</FooterText>
      </Footer>
    </Container>
  );
};

export default LandingPage;
