// Debug script to test frontend API calls
// Run this in browser console

async function testMonitorAPI() {
    try {
        // Get auth token first
        const loginResponse = await fetch('http://localhost:8000/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: 'admin',
                password: 'admin123'
            })
        });
        
        const loginData = await loginResponse.json();
        console.log('Login response:', loginData);
        
        if (!loginData.access_token) {
            throw new Error('No access token received');
        }
        
        // Test monitor inmate record endpoint
        const inmateResponse = await fetch('http://localhost:8000/monitors/4/inmate-record', {
            headers: {
                'Authorization': `Bearer ${loginData.access_token}`,
                'Content-Type': 'application/json'
            }
        });
        
        const inmateData = await inmateResponse.json();
        console.log('Monitor inmate data:', inmateData);
        
        // Check current incarceration
        const currentIncarceration = inmateData.incarceration_records?.find(record => record.actual_status === 'in_custody');
        console.log('Current incarceration:', currentIncarceration);
        
        return inmateData;
        
    } catch (error) {
        console.error('API test failed:', error);
    }
}

// Run the test
testMonitorAPI();
