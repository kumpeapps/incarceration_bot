import React from 'react';
import { useParams } from 'react-router-dom';
import { Typography, Box } from '@mui/material';

const InmateDetailPage: React.FC = () => {
  const { id } = useParams();

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Inmate Details - ID: {id}
      </Typography>
      <Typography>
        Detailed inmate information will be displayed here.
      </Typography>
    </Box>
  );
};

export default InmateDetailPage;
