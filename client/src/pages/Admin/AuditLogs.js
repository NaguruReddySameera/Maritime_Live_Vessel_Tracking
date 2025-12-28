import React from 'react';
import { Container, Typography } from '@mui/material';

const AuditLogs = () => {
  return (
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom>Audit Logs</Typography>
      <Typography variant="body1">Admin only</Typography>
    </Container>
  );
};

export default AuditLogs;
