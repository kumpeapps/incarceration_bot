// Runtime configuration utility

interface RuntimeConfig {
  API_BASE_URL: string;
  APP_TITLE: string;
}

interface WindowWithConfig extends Window {
  runtimeConfig?: RuntimeConfig;
}

export const getConfig = () => {
  const windowWithConfig = window as WindowWithConfig;
  
  // Use runtime config if available, fallback to environment variables for development
  return {
    API_BASE_URL: windowWithConfig.runtimeConfig?.API_BASE_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
    APP_TITLE: windowWithConfig.runtimeConfig?.APP_TITLE || import.meta.env.VITE_APP_TITLE || 'Incarceration Bot Dashboard'
  };
};
