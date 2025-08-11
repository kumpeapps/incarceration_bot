import { getConfig } from '../config/runtime';

export function ConfigTest() {
  const config = getConfig();
  
  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h2>Configuration Test</h2>
      <pre>{JSON.stringify(config, null, 2)}</pre>
      <h3>Environment Variables</h3>
      <pre>{JSON.stringify({
        VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
        VITE_APP_TITLE: import.meta.env.VITE_APP_TITLE,
        DEV: import.meta.env.DEV,
        PROD: import.meta.env.PROD
      }, null, 2)}</pre>
      <h3>Window Runtime Config</h3>
      <pre>{JSON.stringify((window as any).runtimeConfig, null, 2)}</pre>
    </div>
  );
}
