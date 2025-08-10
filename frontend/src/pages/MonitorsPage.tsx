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
  TablePagination,
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
  NotificationsActive,
  NotificationsOff,
  Email,
  Sms,
  Notifications,
  AssignmentInd,
  Link,
  Visibility,
} from '@mui/icons-material';
import { apiService } from '../services/api';
import { Monitor, PaginatedResponse, MonitorSearchParams } from '../types';

interface MonitorFormData {
  name: string;
  notify_address: string;
  notify_method: string;
  enable_notifications: number;
}

const MonitorsPage: React.FC = () => {
  const [monitors, setMonitors] = useState<Monitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [total, setTotal] = useState(0);
  
  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingMonitor, setEditingMonitor] = useState<Monitor | null>(null);
  const [formData, setFormData] = useState<MonitorFormData>({
    name: '',
    notify_address: '',
    notify_method: 'pushover',
    enable_notifications: 1,
  });
  const [formLoading, setFormLoading] = useState(false);

  const fetchMonitors = async (searchParams: MonitorSearchParams = {}) => {
    try {
      setLoading(true);
      setError(null);
      
      const params: MonitorSearchParams = {
        page: page + 1,
        limit: rowsPerPage,
        ...searchParams,
      };

      const response: PaginatedResponse<Monitor> = await apiService.getMonitors(params);
      setMonitors(response.items);
      setTotal(response.total);
    } catch (err) {
      console.error('Failed to fetch monitors:', err);
      setError('Failed to load monitors');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMonitors();
  }, [page, rowsPerPage]);

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleOpenDialog = (monitor?: Monitor) => {
    if (monitor) {
      setEditingMonitor(monitor);
      setFormData({
        name: monitor.name,
        notify_address: monitor.notify_address,
        notify_method: monitor.notify_method || 'pushover',
        enable_notifications: monitor.enable_notifications,
      });
    } else {
      setEditingMonitor(null);
      setFormData({
        name: '',
        notify_address: '',
        notify_method: 'pushover',
        enable_notifications: 1,
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingMonitor(null);
    setFormData({
      name: '',
      notify_address: '',
      notify_method: 'pushover',
      enable_notifications: 1,
    });
  };

  const handleSubmit = async () => {
    try {
      setFormLoading(true);
      
      if (editingMonitor) {
        await apiService.updateMonitor(editingMonitor.id, formData);
      } else {
        await apiService.createMonitor(formData);
      }
      
      handleCloseDialog();
      fetchMonitors();
    } catch (err) {
      console.error('Failed to save monitor:', err);
      setError(`Failed to ${editingMonitor ? 'update' : 'create'} monitor`);
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async (monitor: Monitor) => {
    if (window.confirm(`Are you sure you want to delete the monitor for "${monitor.name}"?`)) {
      try {
        await apiService.deleteMonitor(monitor.id);
        fetchMonitors();
      } catch (err) {
        console.error('Failed to delete monitor:', err);
        setError('Failed to delete monitor');
      }
    }
  };

  const handleViewInmateRecord = async (monitor: Monitor) => {
    try {
      setLoading(true);
      const inmateRecord = await apiService.getMonitorInmateRecord(monitor.id);
      // Show the inmate record in a dialog or navigate to a detail page
      alert(`Inmate Record for ${monitor.name}:\n${JSON.stringify(inmateRecord, null, 2)}`);
    } catch (err) {
      console.error('Failed to fetch inmate record:', err);
      setError('Failed to fetch inmate record');
    } finally {
      setLoading(false);
    }
  };

  const handleAssignMonitor = async (monitor: Monitor) => {
    const userId = prompt(`Enter User ID to assign monitor "${monitor.name}" to:`);
    if (userId && !isNaN(Number(userId))) {
      try {
        await apiService.assignMonitor(monitor.id, Number(userId));
        setError(null);
        alert(`Monitor "${monitor.name}" assigned to user ${userId}`);
        fetchMonitors();
      } catch (err) {
        console.error('Failed to assign monitor:', err);
        setError('Failed to assign monitor');
      }
    }
  };

  const handleLinkMonitor = async (monitor: Monitor) => {
    const linkedMonitorId = prompt(`Enter Monitor ID to link with "${monitor.name}":`);
    const reason = prompt(`Enter reason for linking (optional):`);
    
    if (linkedMonitorId && !isNaN(Number(linkedMonitorId))) {
      try {
        await apiService.linkMonitors(monitor.id, Number(linkedMonitorId), reason || undefined);
        setError(null);
        alert(`Monitor "${monitor.name}" linked to monitor ${linkedMonitorId}`);
        fetchMonitors();
      } catch (err) {
        console.error('Failed to link monitor:', err);
        setError('Failed to link monitor');
      }
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr || dateStr === '') return 'N/A';
    try {
      return new Date(dateStr).toLocaleDateString();
    } catch {
      return dateStr;
    }
  };

  const getNotificationIcon = (method?: string) => {
    switch (method?.toLowerCase()) {
      case 'email':
        return <Email />;
      case 'sms':
        return <Sms />;
      case 'pushover':
      default:
        return <Notifications />;
    }
  };

  const getStatusChip = (monitor: Monitor) => {
    const isActive = monitor.enable_notifications === 1;
    return (
      <Chip
        icon={isActive ? <NotificationsActive /> : <NotificationsOff />}
        label={isActive ? 'Active' : 'Disabled'}
        color={isActive ? 'success' : 'default'}
        size="small"
      />
    );
  };

  if (loading && monitors.length === 0) {
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
          Monitors ({total.toLocaleString()})
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleOpenDialog()}
        >
          Add Monitor
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
        Monitors track specific individuals and send notifications when their status changes.
      </Typography>

      {/* Results Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Notification Method</TableCell>
              <TableCell>Notify Address</TableCell>
              <TableCell>Last Seen</TableCell>
              <TableCell>Arrest Date</TableCell>
              <TableCell>Release Date</TableCell>
              <TableCell>Jail</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <CircularProgress size={24} />
                </TableCell>
              </TableRow>
            ) : monitors.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <Typography color="textSecondary">
                    No monitors found. Click "Add Monitor" to create your first monitor.
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              monitors.map((monitor) => (
                <TableRow key={monitor.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {monitor.name}
                    </Typography>
                  </TableCell>
                  <TableCell>{getStatusChip(monitor)}</TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      {getNotificationIcon(monitor.notify_method)}
                      <Typography variant="body2">
                        {monitor.notify_method || 'pushover'}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {monitor.notify_address}
                    </Typography>
                  </TableCell>
                  <TableCell>{formatDate(monitor.last_seen_incarcerated)}</TableCell>
                  <TableCell>{formatDate(monitor.arrest_date)}</TableCell>
                  <TableCell>{formatDate(monitor.release_date)}</TableCell>
                  <TableCell>{monitor.jail || 'N/A'}</TableCell>
                  <TableCell align="right">
                    <Tooltip title="View as Inmate Record">
                      <IconButton size="small" onClick={() => handleViewInmateRecord(monitor)}>
                        <Visibility />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Assign to User">
                      <IconButton size="small" onClick={() => handleAssignMonitor(monitor)}>
                        <AssignmentInd />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Link Monitor">
                      <IconButton size="small" onClick={() => handleLinkMonitor(monitor)}>
                        <Link />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit">
                      <IconButton size="small" onClick={() => handleOpenDialog(monitor)}>
                        <Edit />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton size="small" onClick={() => handleDelete(monitor)} color="error">
                        <Delete />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[10, 25, 50, 100]}
          component="div"
          count={total}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TableContainer>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingMonitor ? 'Edit Monitor' : 'Add New Monitor'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Person's Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                helperText="Enter the full name of the person to monitor"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Notification Method</InputLabel>
                <Select
                  value={formData.notify_method}
                  label="Notification Method"
                  onChange={(e) => setFormData({ ...formData, notify_method: e.target.value })}
                >
                  <MenuItem value="pushover">Pushover</MenuItem>
                  <MenuItem value="email">Email</MenuItem>
                  <MenuItem value="sms">SMS</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Status</InputLabel>
                <Select
                  value={formData.enable_notifications}
                  label="Status"
                  onChange={(e) => setFormData({ ...formData, enable_notifications: Number(e.target.value) })}
                >
                  <MenuItem value={1}>Active</MenuItem>
                  <MenuItem value={0}>Disabled</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Notification Address"
                value={formData.notify_address}
                onChange={(e) => setFormData({ ...formData, notify_address: e.target.value })}
                required
                helperText={
                  formData.notify_method === 'email' 
                    ? 'Enter email address'
                    : formData.notify_method === 'sms'
                    ? 'Enter phone number'
                    : 'Enter Pushover user key'
                }
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained"
            disabled={formLoading || !formData.name || !formData.notify_address}
          >
            {formLoading ? <CircularProgress size={24} /> : editingMonitor ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MonitorsPage;
