import React from 'react';
import styled from '@emotion/styled';

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
`;

const Box = styled.div`
  padding: 2rem 0;
`;

const Title = styled.h1`
  font-size: 2rem;
  margin: 0 0 1rem 0;
  color: #1f2937;
  font-weight: 600;
`;

const Description = styled.p`
  color: #6b7280;
  font-size: 1rem;
`;

const SettingsPage: React.FC = () => {
  return (
    <Container>
      <Box>
        <Title>Settings</Title>
        <Description>Settings functionality coming soon...</Description>
      </Box>
    </Container>
  );
};

export default SettingsPage;
