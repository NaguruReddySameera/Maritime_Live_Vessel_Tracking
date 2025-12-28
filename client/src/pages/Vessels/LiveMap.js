import React from 'react';
import { Container, Typography } from '@mui/material';

const LiveMap = () => {
  return (
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom>Live Vessel Map</Typography>
      <Typography variant="body1">Interactive map with real-time vessel positions will be displayed here using React-Leaflet.</Typography>
    </Container>
  );
};

export default LiveMap;
