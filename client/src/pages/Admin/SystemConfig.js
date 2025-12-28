import React from 'react';
import { Container, Typography } from '@mui/material';

const SystemConfig = () => {
  return (
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom>System Configuration</Typography>
      <Typography variant="body1">Admin only</Typography>
    </Container>
  );
};

export default SystemConfig;
