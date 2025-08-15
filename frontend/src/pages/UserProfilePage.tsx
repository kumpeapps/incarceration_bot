import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  Grid,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  CardActions,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
} from '@mui/material';
import {
  Person,
  Lock,
  Key,
  Security,
  Group,
  AdminPanelSettings,
  ContentCopy,
} from '@mui/icons-material';
import { apiService } from '../services/api';
import { User } from '../types';

const UserProfilePage: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Password change state
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [passwordLoading, setPasswordLoading] = useState(false);
  
  // API key state
  const [apiKeyDialogOpen, setApiKeyDialogOpen] = useState(false);
  const [generatedApiKey, setGeneratedApiKey] = useState<string | null>(null);
  const [apiKeyLoading, setApiKeyLoading] = useState(false);

  useEffect(() => {
    fetchUserProfile();
  }, []);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      const user = await apiService.getCurrentUser();
      setCurrentUser(user);
    } catch (err) {
      console.error('Failed to fetch user profile:', err);
      setError('Failed to load user profile');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async () => {
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    if (passwordForm.newPassword.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }

    try {
      setPasswordLoading(true);
      setError(null);
      
      await apiService.changePassword({
        currentPassword: passwordForm.currentPassword,
        newPassword: passwordForm.newPassword,
      });
      
      setPasswordDialogOpen(false);
      setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
      setError(null);
      // You could add a success message here
    } catch (err) {
      console.error('Failed to change password:', err);
      setError('Failed to change password. Please check your current password.');
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleGenerateApiKey = async () => {
    if (!currentUser?.groups?.some(g => g.name === 'api')) {
      setError('You need to be in the "api" group to request API keys. Please contact an administrator.');
      return;
    }

    try {
      setApiKeyLoading(true);
      setError(null);
      
      const response = await apiService.generateMyApiKey();
      setGeneratedApiKey(response.api_key);
    } catch (err) {
      console.error('Failed to generate API key:', err);
      setError('Failed to generate API key');
    } finally {
      setApiKeyLoading(false);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      // You could add a toast notification here
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return 'Invalid date';
    }
  };

  const getGroupColor = (groupName: string) => {
    switch (groupName) {
      case 'admin': return 'primary';
      case 'moderator': return 'secondary';
      case 'api': return 'info';
      case 'banned': return 'error';
      case 'locked': return 'warning';
      default: return 'default';
    }
  };

  const getGroupIcon = (groupName: string) => {
    switch (groupName) {
      case 'admin': return <AdminPanelSettings />;
      case 'api': return <Key />;
      case 'banned': return <Lock />;
      case 'locked': return <Lock />;
      default: return <Group />;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (!currentUser) {
    return (
      <Box p={3}>
        <Alert severity="error">Failed to load user profile</Alert>
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        My Profile
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Basic Information */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <Person sx={{ mr: 1 }} />
                Basic Information
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="textSecondary">Username</Typography>
                <Typography variant="body1">{currentUser.username}</Typography>
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="textSecondary">Email</Typography>
                <Typography variant="body1">{currentUser.email}</Typography>
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="textSecondary">Role</Typography>
                <Typography variant="body1" sx={{ textTransform: 'capitalize' }}>
                  {currentUser.role}
                </Typography>
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="textSecondary">Account Created</Typography>
                <Typography variant="body1">{formatDate(currentUser.created_at)}</Typography>
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="textSecondary">Last Login</Typography>
                <Typography variant="body1">
                  {currentUser.last_login ? formatDate(currentUser.last_login) : 'Never'}
                </Typography>
              </Box>
            </CardContent>
            <CardActions>
              <Button
                startIcon={<Lock />}
                onClick={() => setPasswordDialogOpen(true)}
                variant="outlined"
              >
                Change Password
              </Button>
            </CardActions>
          </Card>
        </Grid>

        {/* Groups and Permissions */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <Security sx={{ mr: 1 }} />
                Groups & Permissions
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Your Groups
                </Typography>
                {currentUser.groups && currentUser.groups.length > 0 ? (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {currentUser.groups.map((group) => (
                      <Chip
                        key={group.id}
                        label={group.name}
                        icon={getGroupIcon(group.name)}
                        color={getGroupColor(group.name) as any}
                        variant="outlined"
                      />
                    ))}
                  </Box>
                ) : (
                  <Typography variant="body2" color="textSecondary">
                    No groups assigned
                  </Typography>
                )}
              </Box>
              
              {currentUser.groups?.some(g => g.name === 'api') && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    API Access
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    You have API access permissions. You can generate API keys for programmatic access.
                  </Typography>
                  
                  {currentUser.api_key && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="textSecondary">Current API Key</Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {currentUser.api_key.substring(0, 8)}...
                        </Typography>
                        <Button
                          size="small"
                          startIcon={<ContentCopy />}
                          onClick={() => copyToClipboard(currentUser.api_key!)}
                        >
                          Copy
                        </Button>
                      </Box>
                    </Box>
                  )}
                </Box>
              )}
            </CardContent>
            
            {currentUser.groups?.some(g => g.name === 'api') && (
              <CardActions>
                <Button
                  startIcon={<Key />}
                  onClick={() => setApiKeyDialogOpen(true)}
                  variant="outlined"
                  color="primary"
                >
                  {currentUser.api_key ? 'Generate New API Key' : 'Generate API Key'}
                </Button>
              </CardActions>
            )}
          </Card>
        </Grid>
      </Grid>

      {/* Password Change Dialog */}
      <Dialog open={passwordDialogOpen} onClose={() => setPasswordDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Change Password</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Current Password"
                type="password"
                value={passwordForm.currentPassword}
                onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="New Password"
                type="password"
                value={passwordForm.newPassword}
                onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                required
                helperText="Password must be at least 6 characters long"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Confirm New Password"
                type="password"
                value={passwordForm.confirmPassword}
                onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                required
                error={passwordForm.confirmPassword !== '' && passwordForm.newPassword !== passwordForm.confirmPassword}
                helperText={passwordForm.confirmPassword !== '' && passwordForm.newPassword !== passwordForm.confirmPassword ? 'Passwords do not match' : ''}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPasswordDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handlePasswordChange}
            variant="contained"
            disabled={passwordLoading || !passwordForm.currentPassword || !passwordForm.newPassword || !passwordForm.confirmPassword}
          >
            {passwordLoading ? <CircularProgress size={24} /> : 'Change Password'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* API Key Generation Dialog */}
      <Dialog open={apiKeyDialogOpen} onClose={() => setApiKeyDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Generate API Key</DialogTitle>
        <DialogContent>
          {apiKeyLoading ? (
            <Box display="flex" alignItems="center" justifyContent="center" py={4}>
              <CircularProgress />
              <Typography sx={{ ml: 2 }}>Generating API key...</Typography>
            </Box>
          ) : generatedApiKey ? (
            <Box>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                New API key generated successfully. Please copy and save this key as it won't be shown again.
              </Typography>
              <TextField
                fullWidth
                value={generatedApiKey}
                variant="outlined"
                InputProps={{
                  readOnly: true,
                  sx: { fontFamily: 'monospace' }
                }}
                sx={{ mt: 2 }}
              />
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
                <Button
                  startIcon={<ContentCopy />}
                  onClick={() => copyToClipboard(generatedApiKey)}
                  variant="outlined"
                >
                  Copy to Clipboard
                </Button>
              </Box>
            </Box>
          ) : (
            <Box>
              <Typography variant="body2" gutterBottom>
                This will generate a new API key for your account. If you already have an API key, 
                it will be replaced with this new one.
              </Typography>
              <Typography variant="body2" color="textSecondary">
                API keys are used for programmatic access to the system.
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApiKeyDialogOpen(false)}>
            {generatedApiKey ? 'Close' : 'Cancel'}
          </Button>
          {!generatedApiKey && (
            <Button 
              onClick={handleGenerateApiKey}
              variant="contained"
              disabled={apiKeyLoading}
            >
              Generate API Key
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserProfilePage;
