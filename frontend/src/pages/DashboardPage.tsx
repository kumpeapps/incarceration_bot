import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  People,
  Security,
  Business,
  TrendingUp,
  LocationOn,
  Notifications,
} from '@mui/icons-material';
import { apiService } from '../services/api';
import { DashboardStats } from '../types';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color, subtitle }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography color="textSecondary" gutterBottom variant="overline">
            {title}
          </Typography>
          <Typography variant="h4" component="h2">
            {value}
          </Typography>
          {subtitle && (
            <Typography variant="body2" color="textSecondary">
              {subtitle}
            </Typography>
          )}
        </Box>
        <Box sx={{ color, fontSize: 40 }}>
          {icon}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        setError(null);
        const dashboardStats = await apiService.getDashboardStats();
        setStats(dashboardStats);
      } catch (err) {
        console.error('Failed to fetch dashboard stats:', err);
        setError('Failed to load dashboard statistics');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  if (!stats) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        <Alert severity="warning">No data available</Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Inmates"
            value={stats.total_inmates}
            subtitle={`${stats.total_active_inmates} currently in custody`}
            icon={<People />}
            color="#1976d2"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Monitors"
            value={stats.total_monitors}
            subtitle="Monitoring for changes"
            icon={<Security />}
            color="#dc004e"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Jails"
            value={`${stats.active_jails}/${stats.total_jails}`}
            subtitle="Active jails being monitored"
            icon={<Business />}
            color="#ed6c02"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Recent Activity"
            value={`+${stats.recent_arrests}`}
            subtitle={`${stats.recent_releases} releases`}
            icon={<TrendingUp />}
            color="#2e7d32"
          />
        </Grid>
      </Grid>
      
      <Grid container spacing={3} sx={{ mt: 3 }}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Quick Stats
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Box display="flex" alignItems="center" mb={2}>
                  <LocationOn sx={{ mr: 1, color: '#1976d2' }} />
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Active Custody Rate
                    </Typography>
                    <Typography variant="h6">
                      {stats.total_inmates > 0 
                        ? Math.round((stats.total_active_inmates / stats.total_inmates) * 100)
                        : 0}%
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Box display="flex" alignItems="center" mb={2}>
                  <Notifications sx={{ mr: 1, color: '#dc004e' }} />
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Monitor Coverage
                    </Typography>
                    <Typography variant="h6">
                      {stats.total_inmates > 0 
                        ? Math.round((stats.total_monitors / stats.total_inmates) * 100)
                        : 0}%
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              System Status
            </Typography>
            <Box display="flex" alignItems="center" mb={2}>
              <Box 
                sx={{ 
                  width: 12, 
                  height: 12, 
                  borderRadius: '50%', 
                  backgroundColor: '#4caf50',
                  mr: 2 
                }} 
              />
              <Typography variant="body2">
                API Status: Online
              </Typography>
            </Box>
            <Box display="flex" alignItems="center" mb={2}>
              <Box 
                sx={{ 
                  width: 12, 
                  height: 12, 
                  borderRadius: '50%', 
                  backgroundColor: stats.active_jails > 0 ? '#4caf50' : '#f44336',
                  mr: 2 
                }} 
              />
              <Typography variant="body2">
                Data Collection: {stats.active_jails > 0 ? 'Active' : 'Inactive'}
              </Typography>
            </Box>
            <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
              Last updated: {new Date().toLocaleTimeString()}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardPage;
