import React from 'react';
import { Container, Typography } from '@mui/material';

const UserManagement = () => {
  return (
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom>User Management</Typography>
      <Typography variant="body1">Admin only</Typography>
    </Container>
  );
};

export default UserManagement;
