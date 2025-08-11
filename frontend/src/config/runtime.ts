// Runtime configuration utility
declare global {
  interface Window {
    runtimeConfig?: {
      API_BASE_URL: string;
      APP_TITLE: string;
    };
  }
}

export const getConfig = () => {
  // Use runtime config if available, fallback to environment variables for development
  return {
    API_BASE_URL: window.runtimeConfig?.API_BASE_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
    APP_TITLE: window.runtimeConfig?.APP_TITLE || import.meta.env.VITE_APP_TITLE || 'Incarceration Bot Dashboard'
  };
};
