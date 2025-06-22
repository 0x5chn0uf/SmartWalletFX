import React from 'react';
import {
  HeroSection,
  WalletConnectCTA,
  FeaturedStats,
  RecentActivityList,
  TrustBanner,
} from '../components/home';

const HomePage: React.FC = () => {
  return (
    <div>
      <HeroSection />
      <WalletConnectCTA />
      <FeaturedStats />
      <RecentActivityList />
      <TrustBanner />
    </div>
  );
};

export default HomePage; 