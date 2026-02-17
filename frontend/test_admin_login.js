// Test Admin Login - Copy and paste this ENTIRE block into browser console
// Replace the email and password with your admin credentials

const testAdminLogin = async () => {
  const adminEmail = 'admin@example.com';  // ⚠️ REPLACE WITH YOUR ADMIN EMAIL
  const adminPassword = 'Admin123!';        // ⚠️ REPLACE WITH YOUR ADMIN PASSWORD
  
  console.log('=== MANUAL ADMIN LOGIN TEST START ===');
  console.log('Email:', adminEmail);
  console.log('Password length:', adminPassword.length);
  
  // Test 1: Check if fetch is available
  console.log('Test 1: Checking fetch availability...');
  if (typeof fetch === 'undefined') {
    console.error('ERROR: fetch is not available!');
    return;
  }
  console.log('✓ fetch is available');
  
  // Test 2: Check URL
  const url = 'http://localhost:5001/api/auth/login';
  console.log('Test 2: URL:', url);
  
  // Test 3: Create request body
  const requestBody = JSON.stringify({
    email: adminEmail,
    password: adminPassword
  });
  console.log('Test 3: Request body created, length:', requestBody.length);
  
  // Test 4: Make the request with timeout
  console.log('Test 4: Making fetch request (with 10s timeout)...');
  
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: requestBody,
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    console.log('Test 5: Response received!');
    console.log('Status:', response.status);
    console.log('StatusText:', response.statusText);
    console.log('OK?', response.ok);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Response not OK! Error:', errorText);
      return;
    }
    
    const data = await response.json();
    console.log('Test 6: JSON parsed');
    console.log('Response data:', data);
    
    if (data.access_token) {
      console.log('Test 7: Token found!');
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      console.log('✓ Stored in localStorage');
      console.log('User role:', data.user?.role);
      window.location.href = '/dashboard';
    } else {
      console.error('ERROR: No access_token!');
      console.error('Data:', JSON.stringify(data, null, 2));
    }
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      console.error('ERROR: Request timed out after 10 seconds!');
    } else {
      console.error('ERROR:', error.name, error.message);
      console.error('Stack:', error.stack);
    }
  }
  
  console.log('=== TEST COMPLETE ===');
};

// Run the test
testAdminLogin();

