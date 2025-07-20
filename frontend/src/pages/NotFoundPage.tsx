import React from 'react';
import styled from '@emotion/styled';
import { useNavigate } from 'react-router-dom';
import { FiAlertTriangle } from 'react-icons/fi';

const Container = styled.div`
  max-width: 600px;
  margin: 0 auto;
  padding: 0 1rem;
`;

const Box = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  text-align: center;
  gap: 1.5rem;
`;

const IconWrapper = styled.div`
  font-size: 120px;
  color: #ef4444;
`;

const Title = styled.h1`
  font-size: 4rem;
  font-weight: bold;
  margin: 0;
  color: #1f2937;
`;

const Subtitle = styled.h2`
  font-size: 1.5rem;
  margin: 0 0 1rem 0;
  color: #374151;
`;

const Description = styled.p`
  color: #6b7280;
  margin-bottom: 2rem;
  font-size: 1rem;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  justify-content: center;
`;

const Button = styled.button<{ variant?: 'contained' | 'outlined' }>`
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid;

  ${props =>
    props.variant === 'contained'
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
    color: #3b82f6;
    border-color: #3b82f6;
    
    &:hover {
      background: #eff6ff;
    }
  `}
`;

const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  const handleGoHome = () => {
    navigate('/');
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  return (
    <Container>
      <Box>
        <IconWrapper>
          <FiAlertTriangle />
        </IconWrapper>

        <Title>404</Title>

        <Subtitle>Page Not Found</Subtitle>

        <Description>The page you're looking for doesn't exist or has been moved.</Description>

        <ButtonGroup>
          <Button variant="contained" onClick={handleGoHome}>
            Go Home
          </Button>

          <Button variant="outlined" onClick={handleGoBack}>
            Go Back
          </Button>
        </ButtonGroup>
      </Box>
    </Container>
  );
};

export default NotFoundPage;
