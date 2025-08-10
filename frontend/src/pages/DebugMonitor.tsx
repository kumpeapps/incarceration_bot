import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Typography, Box, Card, CardContent } from '@mui/material';
import { apiService } from '../services/api';

const DebugMonitor: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const monitorId = parseInt(id || '0');
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiService.getMonitorInmateRecord(monitorId);
        setData(response);
      } catch (err) {
        console.error('Error:', err);
        setData({ error: err instanceof Error ? err.message : 'Unknown error' });
      } finally {
        setLoading(false);
      }
    };

    if (monitorId) {
      fetchData();
    }
  }, [monitorId]);

  if (loading) return <div>Loading...</div>;

  const currentIncarceration = data?.incarceration_records?.find(
    (record: any) => record.actual_status === 'in_custody'
  );

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Debug Monitor {monitorId}
      </Typography>
      
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Raw API Data:
          </Typography>
          <pre style={{ fontSize: '12px', whiteSpace: 'pre-wrap' }}>
            {JSON.stringify(data, null, 2)}
          </pre>
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Current Incarceration Check:
          </Typography>
          <Typography>
            Has incarceration_records: {data?.incarceration_records ? 'YES' : 'NO'}
          </Typography>
          <Typography>
            Records count: {data?.incarceration_records?.length || 0}
          </Typography>
          <Typography>
            Current incarceration found: {currentIncarceration ? 'YES' : 'NO'}
          </Typography>
          {currentIncarceration && (
            <Typography>
              Current record status: {currentIncarceration.actual_status}
            </Typography>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default DebugMonitor;
