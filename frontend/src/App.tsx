import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { store } from './store';
import Layout from './components/Layout';
import PrivateRoute from './components/PrivateRoute';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import InmatesPage from './pages/InmatesPage';
import InmateDetailPage from './pages/InmateDetailPage';
import MonitorsPage from './pages/MonitorsPage';
import MonitorDetailPage from './pages/MonitorDetailPage';
import UsersPage from './pages/UsersPage';
import UserProfilePage from './pages/UserProfilePage';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <PrivateRoute>
                  <Layout />
                </PrivateRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="inmates" element={<InmatesPage />} />
              <Route path="inmates/:id" element={<InmateDetailPage />} />
              <Route path="monitors" element={<MonitorsPage />} />
              <Route path="monitors/:id" element={<MonitorDetailPage />} />
              <Route path="users" element={<UsersPage />} />
              <Route path="profile" element={<UserProfilePage />} />
            </Route>
          </Routes>
        </Router>
      </ThemeProvider>
    </Provider>
  );
}

export default App;
