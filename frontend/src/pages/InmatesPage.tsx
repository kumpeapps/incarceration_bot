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
  TextField,
  Button,
  Chip,
  Avatar,
  Alert,
  CircularProgress,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
} from '@mui/material';
import {
  Search,
  Person,
  Clear,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { Inmate, Jail, PaginatedResponse, InmateSearchParams } from '../types';

const InmatesPage: React.FC = () => {
  const navigate = useNavigate();
  const [inmates, setInmates] = useState<Inmate[]>([]);
  const [jails, setJails] = useState<Jail[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [total, setTotal] = useState(0);
  
  // Search/filter state
  const [nameFilter, setNameFilter] = useState('');
  const [jailFilter, setJailFilter] = useState('');
  const [sexFilter, setSexFilter] = useState('');
  const [raceFilter, setRaceFilter] = useState('');
  const [inCustodyFilter, setInCustodyFilter] = useState('all');
  const [inCustodyDateFilter, setInCustodyDateFilter] = useState('all'); // Default to Today + Historical
  const [hasSearched, setHasSearched] = useState(false);

  const fetchInmates = async (searchParams: InmateSearchParams = {}) => {
    try {
      setLoading(true);
      setError(null);
      
      const params: InmateSearchParams = {
        page: page + 1,
        limit: rowsPerPage,
        ...searchParams,
      };

      if (nameFilter) params.name = nameFilter;
      if (jailFilter) params.jail_id = jailFilter;
      if (sexFilter) params.sex = sexFilter;
      if (raceFilter) params.race = raceFilter;
      if (inCustodyFilter && inCustodyFilter !== 'all') params.in_custody = inCustodyFilter === 'true';
      if (inCustodyDateFilter !== 'all') {
        if (inCustodyDateFilter === 'today') params.current_custody = true;
        else if (inCustodyDateFilter === 'historical') params.current_custody = false;
      }

      const response: PaginatedResponse<Inmate> = await apiService.getInmates(params);
      setInmates(response.items);
      setTotal(response.total);
      setHasSearched(true);
    } catch (err) {
      console.error('Failed to fetch inmates:', err);
      setError('Failed to load inmates');
    } finally {
      setLoading(false);
    }
  };

  const fetchJails = async () => {
    try {
      const jailList = await apiService.getJails();
      setJails(jailList);
    } catch (err) {
      console.error('Failed to fetch jails:', err);
    }
  };

  useEffect(() => {
    fetchJails();
    // Don't load inmates automatically - wait for user to search
  }, []);

  useEffect(() => {
    // Only fetch if we have search parameters or pagination changed after initial search
    if (hasSearched) {
      fetchInmates();
    }
  }, [page, rowsPerPage]);

  const handleSearch = () => {
    setPage(0);
    fetchInmates();
  };

  const handleClearFilters = () => {
    setNameFilter('');
    setJailFilter('');
    setSexFilter('');
    setRaceFilter('');
    setInCustodyFilter('all');
    setInCustodyDateFilter('all'); // Reset to default
    setPage(0);
    setHasSearched(false);
    setInmates([]);
    setTotal(0);
  };

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr || dateStr === '') return 'N/A';
    try {
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
      return date.toLocaleDateString();
    } catch {
      return dateStr;
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

  const getStatusChip = (inmate: Inmate) => {
    // Use exact same logic as detail page for consistency
    const releaseDate = formatDate(inmate.release_date);
    const isInCustody = releaseDate === 'N/A';
    
    const statusLabel = isInCustody ? 'In Custody' : 'Released';
    const statusColor = isInCustody ? 'error' : 'success';
    
    return (
      <Chip
        label={statusLabel}
        color={statusColor}
        size="small"
      />
    );
  };

  const calculateDaysIncarcerated = (inmate: Inmate) => {
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

  if (loading && inmates.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Inmates {hasSearched && `(${total.toLocaleString()})`}
      </Typography>

      {!hasSearched && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body1" gutterBottom>
            <strong>Quick Start:</strong> Use the search filters below to find inmates.
          </Typography>
          <Typography variant="body2">
            💡 <strong>Tip:</strong> Leave filters empty and click "Search" to see all current custody records, or use specific filters to narrow your search.
          </Typography>
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Search and Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label="Search by Name"
              value={nameFilter}
              onChange={(e) => setNameFilter(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleSearch();
                }
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth>
              <InputLabel>Jail</InputLabel>
              <Select
                value={jailFilter}
                label="Jail"
                onChange={(e) => setJailFilter(e.target.value)}
              >
                <MenuItem value="">All Jails</MenuItem>
                {jails.map((jail) => (
                  <MenuItem key={jail.jail_id} value={jail.jail_id}>
                    {jail.jail_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={inCustodyFilter}
                label="Status"
                onChange={(e) => setInCustodyFilter(e.target.value)}
              >
                <MenuItem value="all">All Statuses</MenuItem>
                <MenuItem value="true">In Custody</MenuItem>
                <MenuItem value="false">Released</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth>
              <InputLabel>In Custody Date</InputLabel>
              <Select
                value={inCustodyDateFilter}
                label="In Custody Date"
                onChange={(e) => setInCustodyDateFilter(e.target.value)}
              >
                <MenuItem value="all">Today + Historical</MenuItem>
                <MenuItem value="today">Today Only</MenuItem>
                <MenuItem value="historical">Historical</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={1}>
            <FormControl fullWidth>
              <InputLabel>Sex</InputLabel>
              <Select
                value={sexFilter}
                label="Sex"
                onChange={(e) => setSexFilter(e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="M">Male</MenuItem>
                <MenuItem value="F">Female</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={1}>
            <Button
              fullWidth
              variant="contained"
              onClick={handleSearch}
              startIcon={<Search />}
            >
              Search
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Button
              fullWidth
              variant="outlined"
              onClick={handleClearFilters}
              startIcon={<Clear />}
            >
              Clear
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Results Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell></TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Jail</TableCell>
              <TableCell>Cell Block</TableCell>
              <TableCell>Arrest Date</TableCell>
              <TableCell>Days Incarcerated</TableCell>
              <TableCell>Release Date</TableCell>
              <TableCell>Sex</TableCell>
              <TableCell>Race</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={10} align="center">
                  <CircularProgress size={24} />
                </TableCell>
              </TableRow>
            ) : inmates.length === 0 ? (
              <TableRow>
                <TableCell colSpan={10} align="center">
                  <Typography color="textSecondary">
                    {!hasSearched 
                      ? "Use the search filters above and click 'Search' to find inmates"
                      : "No inmates found matching your criteria"
                    }
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              inmates.map((inmate) => (
                <TableRow
                  key={inmate.id}
                  hover
                  onClick={() => navigate(`/inmates/${inmate.id}`)}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell>
                    <Avatar sx={{ width: 32, height: 32 }}>
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
                        <Person />
                      )}
                    </Avatar>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {inmate.name}
                    </Typography>
                  </TableCell>
                  <TableCell>{getStatusChip(inmate)}</TableCell>
                  <TableCell>
                    {jails.find(j => j.jail_id === inmate.jail_id)?.jail_name || inmate.jail_id}
                  </TableCell>
                  <TableCell>{inmate.cell_block || 'N/A'}</TableCell>
                  <TableCell>{formatDate(inmate.arrest_date || '')}</TableCell>
                  <TableCell>
                    <Typography variant="body2" color={inmate.release_date && inmate.release_date !== '' ? 'text.primary' : 'primary.main'}>
                      {calculateDaysIncarcerated(inmate)}
                    </Typography>
                  </TableCell>
                  <TableCell>{formatDate(inmate.release_date)}</TableCell>
                  <TableCell>{inmate.sex}</TableCell>
                  <TableCell>{inmate.race}</TableCell>
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
    </Box>
  );
};

export default InmatesPage;
