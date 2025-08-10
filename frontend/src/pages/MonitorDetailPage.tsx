import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Box,
  Button,
  Chip,
  Alert,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  CardHeader,
  List,
  ListItem,
  ListItemText,
  Divider,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  ArrowBack,
  Edit,
  Link as LinkIcon,
  Person,
  NotificationsActive,
  NotificationsOff,
  History,
  Gavel,
  Add,
  Search,
  Remove,
} from '@mui/icons-material';
import { apiService } from '../services/api';
import { Monitor } from '../types';

interface IncarcerationRecord {
  id: number;
  name: string;
  race: string;
  sex: string;
  cell_block?: string;
  arrest_date?: string;
  held_for_agency?: string;
  mugshot?: string;
  dob: string;
  hold_reasons: string;
  is_juvenile: boolean;
  release_date: string;
  in_custody_date: string;
  jail_id: string;
  hide_record: boolean;
  actual_status: 'in_custody' | 'released';
}

interface MonitorInmateData {
  primary_monitor: Monitor;
  linked_monitors: Monitor[];
  all_names: string[];
  incarceration_records: IncarcerationRecord[];
  total_records: number;
}

interface MonitorInmateLink {
  id: number;
  monitor_id: number;
  inmate_id: number;
  linked_by_user_id: number;
  is_excluded: boolean;
  link_reason?: string;
  created_at: string;
  updated_at: string;
}

interface DetailedInmateLink extends MonitorInmateLink {
  inmate_details?: {
    name: string;
    race: string;
    sex: string;
    dob: string;
    mugshot?: string;
    jail_id: string;
    latest_arrest_date?: string;
    latest_release_date?: string;
    latest_custody_date?: string;
    latest_charges?: string;
    current_status: 'in_custody' | 'released';
  };
}

interface InmateSearchResult {
  id: number;
  name: string;
  dob: string;
  jail_id: string;
  arrest_date?: string;
  actual_status: 'in_custody' | 'released';
  isLinked?: boolean;
}

const MonitorDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const monitorId = parseInt(id || '0');

  const [monitor, setMonitor] = useState<Monitor | null>(null);
  const [inmateData, setInmateData] = useState<MonitorInmateData | null>(null);
  const [detailedInmateLinks, setDetailedInmateLinks] = useState<DetailedInmateLink[]>([]);
  const [inmateHistory, setInmateHistory] = useState<IncarcerationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Monitor linking dialog state
  const [linkDialogOpen, setLinkDialogOpen] = useState(false);
  const [availableMonitors] = useState<Monitor[]>([]);
  const [selectedLinkMonitor, setSelectedLinkMonitor] = useState<number | null>(null);
  const [linkReason, setLinkReason] = useState('');
  
  // Inmate record management dialog state
  const [inmateSearchDialogOpen, setInmateSearchDialogOpen] = useState(false);
  const [inmateSearchQuery, setInmateSearchQuery] = useState('');
  const [inmateSearchResults, setInmateSearchResults] = useState<InmateSearchResult[]>([]);
  const [searchingInmates, setSearchingInmates] = useState(false);
  const [selectedInmate, setSelectedInmate] = useState<InmateSearchResult | null>(null);
  const [linkAction, setLinkAction] = useState<'include' | 'exclude'>('include');
  const [inmateActionReason, setInmateActionReason] = useState('');

  useEffect(() => {
    if (monitorId) {
      fetchMonitorData();
      fetchInmateLinks();
    }
  }, [monitorId]);

  const fetchMonitorData = async () => {
    try {
      setLoading(true);
      const [monitorResponse, inmateResponse] = await Promise.all([
        apiService.getMonitor(monitorId),
        apiService.getMonitorInmateRecord(monitorId)
      ]);
      
      setMonitor(monitorResponse);
      setInmateData(inmateResponse);
    } catch (err) {
      console.error('Failed to fetch monitor data:', err);
      setError('Failed to load monitor details');
    } finally {
      setLoading(false);
    }
  };

  const handleLinkMonitor = async () => {
    if (!selectedLinkMonitor) return;
    
    try {
      await apiService.linkMonitor(monitorId, {
        linked_monitor_id: selectedLinkMonitor,
        link_reason: linkReason
      });
      
      setLinkDialogOpen(false);
      setSelectedLinkMonitor(null);
      setLinkReason('');
      fetchMonitorData(); // Refresh data
    } catch (err) {
      console.error('Failed to link monitor:', err);
      setError('Failed to link monitor');
    }
  };

  const fetchInmateLinks = async () => {
    try {
      const links = await apiService.getMonitorInmateLinks(monitorId);
      
      // Fetch detailed info for each linked inmate
      const detailedLinks: DetailedInmateLink[] = [];
      const allHistory: IncarcerationRecord[] = [];
      
      for (const link of links) {
        try {
          // Get inmate details by ID
          const inmate = await apiService.getInmate(link.inmate_id);
          if (inmate) {
            const detailedLink: DetailedInmateLink = {
              ...link,
              inmate_details: {
                name: inmate.name,
                race: inmate.race || 'Unknown',
                sex: inmate.sex || 'Unknown',
                dob: inmate.dob || 'Unknown',
                mugshot: inmate.mugshot,
                jail_id: inmate.jail_id,
                latest_arrest_date: inmate.arrest_date,
                latest_release_date: inmate.release_date,
                latest_custody_date: inmate.in_custody_date,
                latest_charges: inmate.hold_reasons,
                current_status: (inmate.actual_status || 'released') as 'in_custody' | 'released'
              }
            };
            detailedLinks.push(detailedLink);
            
            // Add this inmate's record to history
            allHistory.push({
              ...inmate,
              actual_status: (inmate.actual_status || 'released') as 'in_custody' | 'released'
            });
          } else {
            // If no details found, add link without details
            detailedLinks.push(link);
          }
        } catch (err) {
          console.error(`Failed to fetch details for inmate ${link.inmate_id}:`, err);
          // Add link without details if fetch fails
          detailedLinks.push(link);
        }
      }
      
      // Deduplicate history records by name and arrest_date
      const deduplicatedHistory = allHistory.reduce((acc, record) => {
        const key = `${record.name}-${record.arrest_date}`;
        if (!acc.find(existing => `${existing.name}-${existing.arrest_date}` === key)) {
          acc.push(record);
        }
        return acc;
      }, [] as IncarcerationRecord[]);
      
      setDetailedInmateLinks(detailedLinks);
      setInmateHistory(deduplicatedHistory);
    } catch (err) {
      console.error('Failed to fetch inmate links:', err);
    }
  };

  const handleSearchInmates = async () => {
    if (!inmateSearchQuery || inmateSearchQuery.length < 2) return;
    
    try {
      setSearchingInmates(true);
      const results = await apiService.searchInmates(inmateSearchQuery);
      
      // Get current linked inmate IDs for this monitor
      const linkedInmateIds = new Set(detailedInmateLinks.map(link => link.inmate_id));
      
      // Map the Inmate[] results to InmateSearchResult[]
      const mappedResults: InmateSearchResult[] = results.map(inmate => ({
        id: inmate.id,
        name: inmate.name,
        dob: inmate.dob,
        jail_id: inmate.jail_id,
        arrest_date: inmate.arrest_date,
        actual_status: inmate.actual_status || ((inmate.release_date && inmate.release_date.trim()) ? 'released' : 'in_custody'),
        isLinked: linkedInmateIds.has(inmate.id)
      }));
      setInmateSearchResults(mappedResults);
    } catch (err) {
      console.error('Failed to search inmates:', err);
      setError('Failed to search inmates');
    } finally {
      setSearchingInmates(false);
    }
  };

  const handleCreateInmateLink = async () => {
    if (!selectedInmate) return;
    
    try {
      // If the inmate is already linked, we need to remove the link
      if (selectedInmate.isLinked) {
        const existingLink = detailedInmateLinks.find(link => link.inmate_id === selectedInmate.id);
        if (existingLink) {
          await apiService.deleteMonitorInmateLink(monitorId, existingLink.id);
        }
      } else {
        // Create a new link
        await apiService.createMonitorInmateLink(monitorId, {
          inmate_id: selectedInmate.id,
          is_excluded: linkAction === 'exclude',
          link_reason: inmateActionReason
        });
      }
      
      setInmateSearchDialogOpen(false);
      setSelectedInmate(null);
      setInmateActionReason('');
      setInmateSearchQuery('');
      setInmateSearchResults([]);
      
      fetchInmateLinks();
      fetchMonitorData(); // Refresh to show updated records
    } catch (err) {
      console.error('Failed to update inmate link:', err);
      setError('Failed to update inmate link');
    }
  };

  const handleDeleteInmateLink = async (linkId: number) => {
    if (!confirm('Are you sure you want to remove this inmate record association?')) return;
    
    try {
      await apiService.deleteMonitorInmateLink(monitorId, linkId);
      fetchInmateLinks();
      fetchMonitorData(); // Refresh to show updated records
    } catch (err) {
      console.error('Failed to delete inmate link:', err);
      setError('Failed to delete inmate link');
    }
  };

  const handleAutoLinkExistingRecords = async () => {
    if (!monitor?.name) return;
    
    try {
      setLoading(true);
      
      // Search for inmates with similar name to the monitor
      const searchResults = await apiService.searchInmates(monitor.name);
      
      if (searchResults.length === 0) {
        alert('No matching inmate records found for auto-linking.');
        return;
      }
      
      // Get existing links to avoid duplicates
      const existingLinks = await apiService.getMonitorInmateLinks(monitorId);
      const existingInmateIds = existingLinks.map(link => link.inmate_id);
      
      // Filter out already linked inmates
      const newRecordsToLink = searchResults.filter(inmate => 
        !existingInmateIds.includes(inmate.id)
      );
      
      if (newRecordsToLink.length === 0) {
        alert('All matching records are already linked to this monitor.');
        return;
      }
      
      // Auto-link each matching record
      const linkPromises = newRecordsToLink.map(inmate =>
        apiService.createMonitorInmateLink(monitorId, {
          inmate_id: inmate.id,
          is_excluded: false,
          link_reason: 'Auto-linked based on name match'
        })
      );
      
      await Promise.all(linkPromises);
      
      // Refresh data
      await fetchInmateLinks();
      await fetchMonitorData();
      
      alert(`Successfully auto-linked ${newRecordsToLink.length} inmate record(s).`);
      
    } catch (err) {
      console.error('Failed to auto-link records:', err);
      setError('Failed to auto-link existing records');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return 'Unknown';
    
    // Parse YYYY-MM-DD format without timezone conversion
    const dateParts = dateString.split('-');
    if (dateParts.length === 3) {
      const year = parseInt(dateParts[0]);
      const month = parseInt(dateParts[1]);
      const day = parseInt(dateParts[2]);
      
      // Create date with explicit timezone-neutral values
      const date = new Date(year, month - 1, day);
      return date.toLocaleDateString();
    }
    
    // Fallback for other formats
    return dateString;
  };

  const getStatusChip = (status: string) => {
    const isInCustody = status === 'in_custody';
    return (
      <Chip
        label={isInCustody ? 'In Custody' : 'Released'}
        color={isInCustody ? 'error' : 'success'}
        size="small"
        icon={isInCustody ? <Gavel /> : <Person />}
      />
    );
  };

  const getCurrentIncarceration = () => {
    return inmateData?.incarceration_records?.find(record => 
      !record.release_date || record.release_date.trim() === ''
    );
  };

  const getPreviousIncarcerations = () => {
    // Get previous incarcerations from monitor's direct inmate data
    const monitorPreviousIncarcerations = inmateData?.incarceration_records?.filter(record => record.actual_status === 'released') || [];
    
    // Combine with linked inmates' history (all records from linked inmates)
    const allIncarcerations = [...monitorPreviousIncarcerations, ...inmateHistory];
    
    // Sort by arrest date (most recent first)
    return allIncarcerations.sort((a, b) => {
      const dateA = new Date(a.arrest_date || '');
      const dateB = new Date(b.arrest_date || '');
      return dateB.getTime() - dateA.getTime();
    });
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !monitor) {
    return (
      <Box p={3}>
        <Alert severity="error">
          {error || 'Monitor not found'}
        </Alert>
        <Button 
          startIcon={<ArrowBack />} 
          onClick={() => navigate('/monitors')}
          sx={{ mt: 2 }}
        >
          Back to Monitors
        </Button>
      </Box>
    );
  }

  const currentIncarceration = getCurrentIncarceration();
  const previousIncarcerations = getPreviousIncarcerations();

  return (
    <Box p={3}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <IconButton onClick={() => navigate('/monitors')}>
            <ArrowBack />
          </IconButton>
          <Typography variant="h4" component="h1">
            Monitor Details: {monitor.name}
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
          <Button
            startIcon={<LinkIcon />}
            onClick={() => setLinkDialogOpen(true)}
            variant="outlined"
          >
            Link Monitor
          </Button>
          <Button
            startIcon={<Edit />}
            variant="contained"
          >
            Edit Monitor
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Monitor Information */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader
              title="Monitor Information"
              avatar={<Person />}
            />
            <CardContent>
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Name"
                    secondary={monitor.name}
                  />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText
                    primary="Notifications"
                    secondary={
                      <Box display="flex" alignItems="center" gap={1}>
                        {monitor.enable_notifications ? (
                          <NotificationsActive color="success" />
                        ) : (
                          <NotificationsOff color="disabled" />
                        )}
                        {monitor.enable_notifications ? 'Enabled' : 'Disabled'}
                      </Box>
                    }
                  />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText
                    primary="Notification Method"
                    secondary={monitor.notify_method}
                  />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText
                    primary="Notification Address"
                    secondary={monitor.notify_address}
                  />
                </ListItem>
                {inmateData?.linked_monitors && inmateData.linked_monitors.length > 0 && (
                  <>
                    <Divider />
                    <ListItem>
                      <ListItemText
                        primary="Linked Monitors"
                        secondary={`${inmateData.linked_monitors.length} linked`}
                      />
                    </ListItem>
                  </>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Current Incarceration */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardHeader
              title="Current Incarceration Status"
              avatar={<Gavel />}
            />
            <CardContent>
              {currentIncarceration ? (
                <Box>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6">
                      Currently In Custody
                    </Typography>
                    {getStatusChip('in_custody')}
                  </Box>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2" color="textSecondary">
                        Jail
                      </Typography>
                      <Typography variant="body1">
                        {currentIncarceration.jail_id}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2" color="textSecondary">
                        Arrest Date
                      </Typography>
                      <Typography variant="body1">
                        {formatDate(currentIncarceration.arrest_date)}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2" color="textSecondary">
                        Held For Agency
                      </Typography>
                      <Typography variant="body1">
                        {currentIncarceration.held_for_agency || 'Unknown'}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2" color="textSecondary">
                        Cell Block
                      </Typography>
                      <Typography variant="body1">
                        {currentIncarceration.cell_block || 'Not specified'}
                      </Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="body2" color="textSecondary">
                        Charges
                      </Typography>
                      <Typography variant="body1">
                        {currentIncarceration.hold_reasons || 'No charges listed'}
                      </Typography>
                    </Grid>
                  </Grid>
                </Box>
              ) : (
                <Box textAlign="center" py={4}>
                  <Typography variant="h6" color="textSecondary">
                    Not Currently In Custody
                  </Typography>
                  <Typography variant="body2" color="textSecondary" mt={1}>
                    This person does not appear to be currently incarcerated
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Previous Incarcerations */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              title={`Previous Incarcerations (${previousIncarcerations.length})`}
              avatar={<History />}
            />
            <CardContent>
              {previousIncarcerations.length > 0 ? (
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Arrest Date</TableCell>
                        <TableCell>Jail</TableCell>
                        <TableCell>Agency</TableCell>
                        <TableCell>Charges</TableCell>
                        <TableCell>Release Date</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {previousIncarcerations.map((record) => (
                        <TableRow key={record.id} hover>
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {record.name || 'Unknown'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={record.actual_status === 'in_custody' ? 'In Custody' : 'Released'}
                              color={record.actual_status === 'in_custody' ? 'error' : 'success'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{formatDate(record.arrest_date)}</TableCell>
                          <TableCell>{record.jail_id}</TableCell>
                          <TableCell>{record.held_for_agency || 'Unknown'}</TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ maxWidth: 300 }}>
                              {record.hold_reasons || 'No charges listed'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            {record.actual_status === 'released' 
                              ? (formatDate(record.release_date) || 'Unknown') 
                              : 'Still in custody'
                            }
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Box textAlign="center" py={4}>
                  <Typography variant="body1" color="textSecondary">
                    No previous incarceration records found
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Inmate Record Management */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              title="Inmate Record Management"
              avatar={<Person />}
              action={
                <Box display="flex" gap={1}>
                  <Button
                    variant="outlined"
                    startIcon={<Add />}
                    onClick={() => setInmateSearchDialogOpen(true)}
                    size="small"
                  >
                    Add/Remove Records
                  </Button>
                  <Button
                    variant="contained"
                    startIcon={<Search />}
                    onClick={handleAutoLinkExistingRecords}
                    size="small"
                    color="primary"
                  >
                    Auto-Link Existing
                  </Button>
                </Box>
              }
            />
            <CardContent>
              <Typography variant="body2" color="textSecondary" mb={2}>
                Manually manage which inmate records are associated with this monitor. 
                Use this to add missed matches or exclude false positives.
              </Typography>

              {detailedInmateLinks.length > 0 ? (
                <Box>
                  {detailedInmateLinks.map((link) => (
                    <Card key={link.id} sx={{ mb: 2, border: '1px solid #e0e0e0' }}>
                      <CardContent>
                        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                          <Box display="flex" alignItems="center" gap={2}>
                            <Chip
                              label={link.is_excluded ? 'Excluded' : 'Included'}
                              color={link.is_excluded ? 'error' : 'success'}
                              size="small"
                              icon={link.is_excluded ? <Remove /> : <Add />}
                            />
                            {link.inmate_details?.current_status && (
                              <Chip
                                label={link.inmate_details.current_status === 'in_custody' ? 'In Custody' : 'Released'}
                                color={link.inmate_details.current_status === 'in_custody' ? 'error' : 'success'}
                                size="small"
                                variant="outlined"
                              />
                            )}
                          </Box>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDeleteInmateLink(link.id)}
                            title="Remove this manual association"
                          >
                            <Remove />
                          </IconButton>
                        </Box>

                        {link.inmate_details ? (
                          <Grid container spacing={2}>
                            {/* Mugshot */}
                            <Grid item xs={12} sm={3} md={2}>
                              {link.inmate_details.mugshot ? (
                                <Box
                                  component="img"
                                  src={`data:image/jpeg;base64,${link.inmate_details.mugshot}`}
                                  alt={`${link.inmate_details.name} mugshot`}
                                  sx={{
                                    width: '100%',
                                    maxWidth: 120,
                                    height: 'auto',
                                    borderRadius: 1,
                                    border: '1px solid #ccc'
                                  }}
                                />
                              ) : (
                                <Box
                                  sx={{
                                    width: '100%',
                                    maxWidth: 120,
                                    height: 160,
                                    backgroundColor: '#f5f5f5',
                                    borderRadius: 1,
                                    border: '1px solid #ccc',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center'
                                  }}
                                >
                                  <Person color="disabled" />
                                </Box>
                              )}
                            </Grid>

                            {/* Inmate Details */}
                            <Grid item xs={12} sm={9} md={10}>
                              <Grid container spacing={2}>
                                <Grid item xs={12} sm={6}>
                                  <Typography variant="h6" gutterBottom>
                                    {link.inmate_details.name}
                                  </Typography>
                                  <Typography variant="body2" color="textSecondary">
                                    <strong>DOB:</strong> {link.inmate_details.dob || 'Unknown'}
                                  </Typography>
                                  <Typography variant="body2" color="textSecondary">
                                    <strong>Race:</strong> {link.inmate_details.race || 'Unknown'}
                                  </Typography>
                                  <Typography variant="body2" color="textSecondary">
                                    <strong>Sex:</strong> {link.inmate_details.sex || 'Unknown'}
                                  </Typography>
                                </Grid>
                                
                                <Grid item xs={12} sm={6}>
                                  <Typography variant="body2" color="textSecondary">
                                    <strong>Jail:</strong> {link.inmate_details.jail_id || 'Unknown'}
                                  </Typography>
                                  <Typography variant="body2" color="textSecondary">
                                    <strong>Latest Arrest:</strong> {formatDate(link.inmate_details.latest_arrest_date)}
                                  </Typography>
                                  <Typography variant="body2" color="textSecondary">
                                    <strong>Custody Date:</strong> {formatDate(link.inmate_details.latest_custody_date)}
                                  </Typography>
                                  {link.inmate_details.latest_charges && (
                                    <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                                      <strong>Latest Charges:</strong><br />
                                      {link.inmate_details.latest_charges}
                                    </Typography>
                                  )}
                                </Grid>
                              </Grid>
                            </Grid>
                          </Grid>
                        ) : (
                          <Typography variant="body2" color="error">
                            Inmate details not available (ID: {link.inmate_id})
                          </Typography>
                        )}

                        <Box mt={2} pt={1} borderTop="1px solid #e0e0e0">
                          <Typography variant="caption" color="textSecondary">
                            <strong>Link Reason:</strong> {link.link_reason || 'No reason provided'} | 
                            <strong> Created:</strong> {formatDate(link.created_at)}
                          </Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              ) : (
                <Box textAlign="center" py={3}>
                  <Typography variant="body2" color="textSecondary">
                    No manual inmate record associations configured
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Use "Add/Remove Records" to manually associate or exclude specific inmate records
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Inmate Search Dialog */}
      <Dialog open={inmateSearchDialogOpen} onClose={() => setInmateSearchDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add/Remove Inmate Records</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" mb={2}>
            Search for inmate records to manually include or exclude from this monitor.
          </Typography>
          
          {/* Search Section */}
          <Box mb={3}>
            <TextField
              fullWidth
              label="Search Inmates by Name"
              value={inmateSearchQuery}
              onChange={(e) => setInmateSearchQuery(e.target.value)}
              placeholder="Enter at least 2 characters"
              InputProps={{
                endAdornment: (
                  <IconButton onClick={handleSearchInmates} disabled={inmateSearchQuery.length < 2}>
                    <Search />
                  </IconButton>
                )
              }}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && inmateSearchQuery.length >= 2) {
                  handleSearchInmates();
                }
              }}
            />
          </Box>

          {/* Search Results */}
          {searchingInmates && (
            <Box display="flex" justifyContent="center" my={2}>
              <CircularProgress size={24} />
            </Box>
          )}

          {inmateSearchResults.length > 0 && (
            <Box mb={3}>
              <Typography variant="subtitle2" mb={1}>Search Results:</Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Name</TableCell>
                      <TableCell>Jail</TableCell>
                      <TableCell>DOB</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Link Status</TableCell>
                      <TableCell>Action</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {inmateSearchResults.map((inmate) => (
                      <TableRow 
                        key={inmate.id}
                        hover
                        selected={selectedInmate?.id === inmate.id}
                        onClick={() => setSelectedInmate(inmate)}
                        style={{ cursor: 'pointer' }}
                      >
                        <TableCell>{inmate.name}</TableCell>
                        <TableCell>{inmate.jail_id}</TableCell>
                        <TableCell>{inmate.dob}</TableCell>
                        <TableCell>{getStatusChip(inmate.actual_status)}</TableCell>
                        <TableCell>
                          {inmate.isLinked ? (
                            <Chip
                              label="Already Linked"
                              color="primary"
                              size="small"
                              variant="outlined"
                            />
                          ) : (
                            <Chip
                              label="Not Linked"
                              color="default"
                              size="small"
                              variant="outlined"
                            />
                          )}
                        </TableCell>
                        <TableCell>
                          <Button
                            size="small"
                            variant={selectedInmate?.id === inmate.id ? "contained" : "outlined"}
                            color={inmate.isLinked ? "error" : "primary"}
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedInmate(inmate);
                              if (inmate.isLinked) {
                                setLinkAction('exclude');
                              } else {
                                setLinkAction('include');
                              }
                            }}
                          >
                            {inmate.isLinked ? 'Remove' : 'Add'}
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}

          {/* Action Selection */}
          {selectedInmate && (
            <Box>
              <Typography variant="subtitle2" mb={1}>
                Selected: {selectedInmate.name} (ID: {selectedInmate.id})
              </Typography>
              
              <FormControl fullWidth margin="normal">
                <InputLabel>Action</InputLabel>
                <Select
                  value={linkAction}
                  onChange={(e) => setLinkAction(e.target.value as 'include' | 'exclude')}
                  label="Action"
                >
                  <MenuItem value="include">Include this record</MenuItem>
                  <MenuItem value="exclude">Exclude this record</MenuItem>
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Reason (Optional)"
                value={inmateActionReason}
                onChange={(e) => setInmateActionReason(e.target.value)}
                margin="normal"
                multiline
                rows={2}
                placeholder={linkAction === 'include' ? 
                  "e.g., This is the same person but wasn't automatically matched" :
                  "e.g., This is a different person with the same name"
                }
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setInmateSearchDialogOpen(false);
            setSelectedInmate(null);
            setInmateActionReason('');
            setInmateSearchQuery('');
            setInmateSearchResults([]);
          }}>
            Cancel
          </Button>
          <Button 
            onClick={handleCreateInmateLink}
            variant="contained"
            disabled={!selectedInmate}
            startIcon={selectedInmate?.isLinked ? <Remove /> : (linkAction === 'include' ? <Add /> : <Remove />)}
            color={selectedInmate?.isLinked ? "error" : "primary"}
          >
            {selectedInmate?.isLinked 
              ? 'Remove Link' 
              : (linkAction === 'include' ? 'Include Record' : 'Exclude Record')
            }
          </Button>
        </DialogActions>
      </Dialog>

      {/* Link Monitor Dialog */}
      <Dialog open={linkDialogOpen} onClose={() => setLinkDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Link Another Monitor</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" mb={2}>
            Link another monitor record that represents the same person.
          </Typography>
          <FormControl fullWidth margin="normal">
            <InputLabel>Select Monitor to Link</InputLabel>
            <Select
              value={selectedLinkMonitor || ''}
              onChange={(e) => setSelectedLinkMonitor(Number(e.target.value))}
              label="Select Monitor to Link"
            >
              {availableMonitors.map((mon) => (
                <MenuItem key={mon.id} value={mon.id}>
                  {mon.name} ({mon.notify_address})
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label="Link Reason (Optional)"
            value={linkReason}
            onChange={(e) => setLinkReason(e.target.value)}
            margin="normal"
            multiline
            rows={3}
            placeholder="e.g., Same person with different name spelling"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLinkDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleLinkMonitor}
            variant="contained"
            disabled={!selectedLinkMonitor}
          >
            Link Monitor
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MonitorDetailPage;
