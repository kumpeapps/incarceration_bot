import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Chip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  Grid,
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  AdminPanelSettings,
  Person,
} from '@mui/icons-material';
import { apiService } from '../services/api';
import { User } from '../types';

interface UserFormData {
  username: string;
  email: string;
  password: string;
  role: 'admin' | 'user';
}

const UsersPage: React.FC = () => {
  // For now, assume admin access - in real app, get from auth context
  const [currentUser] = useState({ id: 1, role: 'admin' });
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [formData, setFormData] = useState<UserFormData>({
    username: '',
    email: '',
    password: '',
    role: 'user',
  });
  const [formLoading, setFormLoading] = useState(false);

  // Check if current user is admin
  const isAdmin = currentUser?.role === 'admin';

  useEffect(() => {
    if (!isAdmin) {
      setError('Access denied. Admin privileges required.');
      setLoading(false);
      return;
    }
    fetchUsers();
  }, [isAdmin]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const userList = await apiService.getUsers();
      setUsers(userList);
    } catch (err) {
      console.error('Failed to fetch users:', err);
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (userToEdit?: User) => {
    if (userToEdit) {
      setEditingUser(userToEdit);
      setFormData({
        username: userToEdit.username,
        email: userToEdit.email,
        password: '', // Don't pre-fill password for editing
        role: userToEdit.role,
      });
    } else {
      setEditingUser(null);
      setFormData({
        username: '',
        email: '',
        password: '',
        role: 'user',
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingUser(null);
    setFormData({
      username: '',
      email: '',
      password: '',
      role: 'user',
    });
  };

  const handleSubmit = async () => {
    try {
      setFormLoading(true);
      
      if (editingUser) {
        // For editing, only send fields that are not empty
        const updateData: Partial<User> = {
          username: formData.username,
          email: formData.email,
          role: formData.role,
        };
        await apiService.updateUser(editingUser.id, updateData);
      } else {
        await apiService.createUser({
          ...formData,
          is_active: true,
        });
      }
      
      handleCloseDialog();
      fetchUsers();
    } catch (err) {
      console.error('Failed to save user:', err);
      setError(`Failed to ${editingUser ? 'update' : 'create'} user`);
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async (userToDelete: User) => {
    if (userToDelete.id === currentUser?.id) {
      setError('You cannot delete your own account');
      return;
    }

    if (window.confirm(`Are you sure you want to delete user "${userToDelete.username}"?`)) {
      try {
        await apiService.deleteUser(userToDelete.id);
        fetchUsers();
      } catch (err) {
        console.error('Failed to delete user:', err);
        setError('Failed to delete user');
      }
    }
  };

  const getRoleChip = (role: string) => {
    return (
      <Chip
        icon={role === 'admin' ? <AdminPanelSettings /> : <Person />}
        label={role === 'admin' ? 'Administrator' : 'User'}
        color={role === 'admin' ? 'primary' : 'default'}
        size="small"
      />
    );
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString();
    } catch {
      return 'N/A';
    }
  };

  if (!isAdmin) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Access Denied
        </Typography>
        <Alert severity="error">
          You do not have permission to access this page. Administrator privileges are required.
        </Alert>
      </Box>
    );
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4" component="h1">
          User Management ({users.length})
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleOpenDialog()}
        >
          Add User
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
        Manage user accounts and permissions for the incarceration bot system.
      </Typography>

      {/* Users Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Username</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Last Login</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography color="textSecondary">
                    No users found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              users.map((userItem) => (
                <TableRow key={userItem.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {userItem.username}
                      {userItem.id === currentUser?.id && (
                        <Chip label="You" size="small" sx={{ ml: 1 }} />
                      )}
                    </Typography>
                  </TableCell>
                  <TableCell>{userItem.email}</TableCell>
                  <TableCell>{getRoleChip(userItem.role)}</TableCell>
                  <TableCell>{formatDate(userItem.created_at)}</TableCell>
                  <TableCell>
                    {userItem.last_login ? formatDate(userItem.last_login) : 'Never'}
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Edit">
                      <IconButton 
                        size="small" 
                        onClick={() => handleOpenDialog(userItem)}
                      >
                        <Edit />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={userItem.id === currentUser?.id ? "Cannot delete your own account" : "Delete"}>
                      <span>
                        <IconButton 
                          size="small" 
                          onClick={() => handleDelete(userItem)} 
                          color="error"
                          disabled={userItem.id === currentUser?.id}
                        >
                          <Delete />
                        </IconButton>
                      </span>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add/Edit User Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingUser ? `Edit User: ${editingUser.username}` : 'Add New User'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Username"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                required
                disabled={!!editingUser} // Don't allow username changes
                helperText={editingUser ? "Username cannot be changed" : "Enter a unique username"}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required={!editingUser}
                helperText={editingUser ? "Leave blank to keep current password" : "Enter a secure password"}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth required>
                <InputLabel>Role</InputLabel>
                <Select
                  value={formData.role}
                  label="Role"
                  onChange={(e) => setFormData({ ...formData, role: e.target.value as 'admin' | 'user' })}
                >
                  <MenuItem value="user">User</MenuItem>
                  <MenuItem value="admin">Administrator</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained"
            disabled={formLoading || !formData.username || !formData.email || (!editingUser && !formData.password)}
          >
            {formLoading ? <CircularProgress size={24} /> : editingUser ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UsersPage;
