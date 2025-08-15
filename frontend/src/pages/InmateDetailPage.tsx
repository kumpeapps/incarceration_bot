import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Avatar,
  Chip,
  Button,
  Alert,
  CircularProgress,
  Divider,
  Card,
  CardContent,
} from '@mui/material';
import {
  ArrowBack,
  Person,
  DateRange,
  Gavel,
  Security,
  Add,
} from '@mui/icons-material';
import { apiService } from '../services/api';
import { Inmate, Jail } from '../types';

const InmateDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [inmate, setInmate] = useState<Inmate | null>(null);
  const [jail, setJail] = useState<Jail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchInmateDetails = async () => {
      if (!id) {
        setError('Invalid record ID');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        
        const inmateData = await apiService.getInmate(parseInt(id));
        setInmate(inmateData);

        // Fetch jail information
        if (inmateData.jail_id) {
          try {
            const jails = await apiService.getJails();
            const jailData = jails.find(j => j.jail_id === inmateData.jail_id);
            setJail(jailData || null);
          } catch (err) {
            console.error('Failed to fetch jail data:', err);
          }
        }
      } catch (err) {
        console.error('Failed to fetch inmate details:', err);
        setError('Failed to load inmate details');
      } finally {
        setLoading(false);
      }
    };

    fetchInmateDetails();
  }, [id]);

  const formatDate = (dateStr?: string) => {
    if (!dateStr || dateStr === '' || dateStr === 'Unknown') return 'N/A';
    try {
      // Handle YYYY-MM-DD format without timezone conversion
      if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
        const dateParts = dateStr.split('-');
        const year = parseInt(dateParts[0]);
        const month = parseInt(dateParts[1]);
        const day = parseInt(dateParts[2]);
        
        // Create date with explicit timezone-neutral values
        const date = new Date(year, month - 1, day);
        
        // Check if date is valid
        if (isNaN(date.getTime())) {
          return 'N/A';
        }
        
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
        });
      }
      
      // Parse date as local date without timezone conversion
      // This prevents 2025-08-08 from being converted to 2025-08-07 due to UTC/local timezone differences
      let date;
      if (dateStr.includes('T')) {
        // Already has time component
        date = new Date(dateStr);
      } else {
        // Date-only string, add local time component
        date = new Date(dateStr + 'T12:00:00');
      }
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        return 'N/A';
      }
      
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return 'N/A';
    }
  };

  const calculateDaysIncarcerated = () => {
    if (!inmate) return 'N/A';
    
    // Use arrest_date as the start date (this is when incarceration began)
    const arrestDateStr = inmate.arrest_date;
    if (!arrestDateStr || arrestDateStr === '' || arrestDateStr === 'Unknown') {
      return 'N/A';
    }

    try {
      // Parse arrest date
      let arrestDate;
      if (arrestDateStr.includes('T')) {
        arrestDate = new Date(arrestDateStr);
      } else {
        arrestDate = new Date(arrestDateStr + 'T00:00:00');
      }

      if (isNaN(arrestDate.getTime())) {
        return 'N/A';
      }

      // Determine end date - either release date or current date
      let endDate;
      const releaseDateStr = inmate.release_date;
      
      if (releaseDateStr && releaseDateStr !== '' && releaseDateStr !== 'Unknown') {
        // Use release date if available
        if (releaseDateStr.includes('T')) {
          endDate = new Date(releaseDateStr);
        } else {
          endDate = new Date(releaseDateStr + 'T23:59:59');
        }
      } else {
        // Still in custody - use current date
        endDate = new Date();
      }

      if (isNaN(endDate.getTime())) {
        return 'N/A';
      }

      // Calculate difference in days
      const timeDiff = endDate.getTime() - arrestDate.getTime();
      const daysDiff = Math.ceil(timeDiff / (1000 * 3600 * 24));

      // Format the result
      if (daysDiff === 1) {
        return '1 day';
      } else if (daysDiff >= 0) {
        return `${daysDiff} days`;
      } else {
        return 'N/A';
      }
    } catch {
      return 'N/A';
    }
  };

  const formatBirthDate = (dobStr?: string) => {
    if (!dobStr || dobStr === '' || dobStr === 'Unknown') return 'N/A';
    
    // Handle various date formats that might come from different jail systems
    try {
      // Try to parse as a regular date first
      let date;
      
      // Handle MM/DD/YYYY format
      if (dobStr.includes('/')) {
        const parts = dobStr.split('/');
        if (parts.length === 3) {
          const month = parseInt(parts[0]) - 1; // Month is 0-indexed
          const day = parseInt(parts[1]);
          const year = parseInt(parts[2]);
          date = new Date(year, month, day);
        }
      }
      // Handle YYYY-MM-DD format
      else if (dobStr.includes('-')) {
        if (dobStr.includes('T')) {
          date = new Date(dobStr);
        } else {
          date = new Date(dobStr + 'T12:00:00');
        }
      }
      // Handle other formats
      else {
        date = new Date(dobStr);
      }
      
      // Check if date is valid
      if (!date || isNaN(date.getTime())) {
        return 'N/A';
      }
      
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return 'N/A';
    }
  };

  const getMugshotSrc = (mugshotData?: string) => {
    if (!mugshotData || mugshotData === '') return null;
    
    // If it's already a data URL (starts with data:), use it directly
    if (mugshotData.startsWith('data:')) {
      return mugshotData;
    }
    
    // If it's base64 encoded image data, create a data URL
    if (mugshotData.length > 100) { // Assume long strings are base64 data
      // Try to detect if it's a JPEG or PNG based on base64 header
      if (mugshotData.startsWith('/9j/') || mugshotData.startsWith('iVBOR')) {
        const mimeType = mugshotData.startsWith('/9j/') ? 'image/jpeg' : 'image/png';
        return `data:${mimeType};base64,${mugshotData}`;
      }
      // Default to JPEG if we can't determine
      return `data:image/jpeg;base64,${mugshotData}`;
    }
    
    // If it's a URL, use it directly
    if (mugshotData.startsWith('http')) {
      return mugshotData;
    }
    
    return null;
  };

  const getStatusChip = () => {
    if (!inmate) return null;
    const isInCustody = inmate.actual_status === 'in_custody' || 
                        (!inmate.actual_status && (!inmate.release_date || inmate.release_date === ''));
    
    return (
      <Chip
        label={isInCustody ? 'In Custody' : 'Released'}
        color={isInCustody ? 'error' : 'success'}
        sx={{ fontSize: '1.1rem', py: 1 }}
      />
    );
  };

  const handleCreateMonitor = () => {
    // Navigate to monitors page with pre-filled name
    navigate('/monitors', { state: { prefillName: inmate?.name } });
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/inmates')}
          sx={{ mb: 2 }}
        >
          Back to Inmates
        </Button>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  if (!inmate) {
    return (
      <Box>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/inmates')}
          sx={{ mb: 2 }}
        >
          Back to Inmates
        </Button>
        <Alert severity="warning">Inmate not found</Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/inmates')}
        >
          Back to Inmates
        </Button>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={handleCreateMonitor}
        >
          Create Monitor
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* Header Card */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Grid container spacing={3} alignItems="center">
              <Grid item>
                <Avatar sx={{ width: 120, height: 120 }}>
                  {getMugshotSrc(inmate.mugshot) ? (
                    <img
                      src={getMugshotSrc(inmate.mugshot)!}
                      alt={inmate.name}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      onError={(e) => {
                        // Hide image if it fails to load and show default avatar
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  ) : (
                    <Person sx={{ fontSize: 60 }} />
                  )}
                </Avatar>
              </Grid>
              <Grid item xs>
                <Typography variant="h4" component="h1" gutterBottom>
                  {inmate.name}
                </Typography>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  {getStatusChip()}
                  {inmate.is_juvenile && (
                    <Chip label="Juvenile" color="warning" />
                  )}
                </Box>
                <Typography variant="body1" color="textSecondary">
                  Record ID: {inmate.id}
                </Typography>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Personal Information */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <Person sx={{ mr: 1, verticalAlign: 'middle' }} />
                Personal Information
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Sex
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {inmate.sex || 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Race
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {inmate.race || 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">
                    Date of Birth
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {formatBirthDate(inmate.dob)}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Custody Information */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <Security sx={{ mr: 1, verticalAlign: 'middle' }} />
                Custody Information
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">
                    Facility
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {jail?.jail_name || inmate.jail_id}
                  </Typography>
                  {jail?.state && (
                    <Typography variant="body2" color="textSecondary">
                      {jail.state}
                    </Typography>
                  )}
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Cell Block
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {inmate.cell_block || 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Held For Agency
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {inmate.held_for_agency || 'N/A'}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Dates */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <DateRange sx={{ mr: 1, verticalAlign: 'middle' }} />
                Important Dates
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">
                    In Custody Date
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {formatDate(inmate.in_custody_date)}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">
                    Arrest Date
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {formatDate(inmate.arrest_date)}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">
                    Release Date
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {(() => {
                      // Prioritize actual_status if available, otherwise use release_date logic
                      if (inmate.actual_status) {
                        return inmate.actual_status === 'in_custody' ? 'Still in custody' : formatDate(inmate.release_date);
                      } else {
                        return formatDate(inmate.release_date) === 'N/A' ? 'Still in custody' : formatDate(inmate.release_date);
                      }
                    })()}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">
                    Days Incarcerated
                  </Typography>
                  <Typography variant="body1" fontWeight="medium" color={inmate.release_date && inmate.release_date !== '' ? 'text.primary' : 'primary.main'}>
                    {calculateDaysIncarcerated()}
                    {(!inmate.release_date || inmate.release_date === '') && (
                      <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                        (ongoing)
                      </Typography>
                    )}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Charges */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <Gavel sx={{ mr: 1, verticalAlign: 'middle' }} />
                Charges & Hold Reasons
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="body1">
                {inmate.hold_reasons || 'No charges listed'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default InmateDetailPage;
