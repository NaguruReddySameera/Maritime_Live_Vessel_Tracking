import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
} from '@mui/material';
import {
  DirectionsBoat,
  Anchor,
  Warning,
  TrendingUp,
} from '@mui/icons-material';
import { fetchVessels } from '../../store/slices/vesselSlice';
import { fetchPorts } from '../../store/slices/portSlice';
import { fetchAlerts } from '../../store/slices/alertSlice';

const Dashboard = () => {
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);
  const { list: vessels } = useSelector((state) => state.vessels);
  const { list: ports } = useSelector((state) => state.ports);
  const { list: alerts } = useSelector((state) => state.alerts);

  useEffect(() => {
    dispatch(fetchVessels({ limit: 10 }));
    dispatch(fetchPorts({ limit: 10 }));
    dispatch(fetchAlerts({ status: 'active' }));
  }, [dispatch]);

  const stats = [
    {
      title: 'Total Vessels',
      value: vessels.length,
      icon: <DirectionsBoat sx={{ fontSize: 40, color: 'primary.main' }} />,
      color: '#1976d2',
    },
    {
      title: 'Ports',
      value: ports.length,
      icon: <Anchor sx={{ fontSize: 40, color: 'success.main' }} />,
      color: '#2e7d32',
    },
    {
      title: 'Active Alerts',
      value: alerts.length,
      icon: <Warning sx={{ fontSize: 40, color: 'warning.main' }} />,
      color: '#ed6c02',
    },
    {
      title: 'On-Time %',
      value: '94%',
      icon: <TrendingUp sx={{ fontSize: 40, color: 'info.main' }} />,
      color: '#0288d1',
    },
  ];

  const underwayVessels = vessels.filter(v => v.status === 'underway').length;
  const atAnchor = vessels.filter(v => v.status === 'at_anchor').length;
  const congestedPorts = ports.filter(p => p.currentCongestion?.status === 'red').length;

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Welcome back, {user?.firstName}!
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {user?.role === 'operator' && 'Monitor your fleet operations'}
          {user?.role === 'analyst' && 'View analytics and insights'}
          {user?.role === 'admin' && 'System overview and management'}
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography color="text.secondary" variant="caption" gutterBottom>
                      {stat.title}
                    </Typography>
                    <Typography variant="h4" component="div">
                      {stat.value}
                    </Typography>
                  </Box>
                  {stat.icon}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Fleet Status
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="body2">Underway:</Typography>
                <Typography variant="body2" fontWeight="bold">{underwayVessels}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="body2">At Anchor:</Typography>
                <Typography variant="body2" fontWeight="bold">{atAnchor}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="body2">Moored:</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {vessels.filter(v => v.status === 'moored').length}
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Port Congestion
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="body2">
                  <Box component="span" sx={{ color: 'error.main', fontWeight: 'bold' }}>●</Box> High Congestion:
                </Typography>
                <Typography variant="body2" fontWeight="bold">{congestedPorts}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="body2">
                  <Box component="span" sx={{ color: 'warning.main', fontWeight: 'bold' }}>●</Box> Medium:
                </Typography>
                <Typography variant="body2" fontWeight="bold">
                  {ports.filter(p => p.currentCongestion?.status === 'yellow').length}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="body2">
                  <Box component="span" sx={{ color: 'success.main', fontWeight: 'bold' }}>●</Box> Normal:
                </Typography>
                <Typography variant="body2" fontWeight="bold">
                  {ports.filter(p => p.currentCongestion?.status === 'green').length}
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Alerts
            </Typography>
            <Box sx={{ mt: 2 }}>
              {alerts.slice(0, 5).map((alert) => (
                <Box
                  key={alert._id}
                  sx={{
                    p: 2,
                    mb: 1,
                    borderLeft: 4,
                    borderColor: alert.severity === 'critical' ? 'error.main' : 'warning.main',
                    bgcolor: 'grey.50',
                  }}
                >
                  <Typography variant="subtitle2">{alert.title}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {alert.message}
                  </Typography>
                </Box>
              ))}
              {alerts.length === 0 && (
                <Typography variant="body2" color="text.secondary">
                  No active alerts
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;
