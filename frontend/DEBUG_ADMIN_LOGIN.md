# Debugging Admin Login Issue

If you're unable to see console logs or API calls when logging in with an admin user, follow these steps:

## Step 1: Verify Browser Console is Open

1. Open DevTools (F12 or Cmd+Option+I on Mac)
2. Go to **Console** tab
3. Make sure console is **not filtered** - check that "All levels" is selected
4. Clear the console (right-click → Clear console)

## Step 2: Test Form Submission

1. Type the admin email in the email field
2. Type the admin password in the password field
3. **Before clicking submit**, check console - you should see:
   - `Login component rendered`
   - `Email input changed:` (when typing email)
   - `Password input changed, length: X` (when typing password)

4. Click the "Sign in" button
5. **Immediately check console** - you should see:
   - `BUTTON CLICKED`
   - `FORM onSubmit handler called`
   - `=== FORM SUBMIT EVENT FIRED ===`
   - `=== LOGIN FORM SUBMITTED ===`

## Step 3: If No Logs Appear

If you don't see ANY logs when clicking the button:

1. **Check for JavaScript errors:**
   - Look for red error messages in console
   - Check if console shows "Paused on exception"

2. **Check Network tab:**
   - Open Network tab in DevTools
   - Try logging in
   - Look for `/api/auth/login` request
   - If it's not there, the request isn't being made

3. **Test with browser console:**
   - Open console
   - Type: `document.querySelector('form').submit()`
   - This will manually submit the form
   - Check if logs appear

4. **Check if form exists:**
   - In console, type: `document.querySelector('form')`
   - Should return the form element
   - If null, the form isn't rendered

## Step 4: Compare Normal User vs Admin User

Try this test:

1. **Clear everything:**
   ```javascript
   localStorage.clear();
   console.clear();
   ```

2. **Login with normal user** - note what you see in console

3. **Logout and clear:**
   ```javascript
   localStorage.clear();
   console.clear();
   ```

4. **Login with admin user** - compare what you see

## Step 5: Manual API Test

Test the API directly from console:

```javascript
// Test admin login API call
fetch('http://localhost:5001/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'admin@example.com',  // Your admin email
    password: 'Admin123!'         // Your admin password
  })
})
.then(response => {
  console.log('Response status:', response.status);
  return response.json();
})
.then(data => {
  console.log('Response data:', data);
  if (data.access_token) {
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    console.log('Token stored!');
    window.location.href = '/dashboard';
  }
})
.catch(error => {
  console.error('Error:', error);
});
```

## Common Issues

1. **Browser extensions blocking requests** - Try incognito mode
2. **Cached JavaScript** - Hard refresh (Cmd+Shift+R or Ctrl+Shift+R)
3. **React DevTools interfering** - Disable React DevTools temporarily
4. **Service worker caching** - Clear service workers in Application tab

## What to Report

If the issue persists, please share:

1. **Browser and version** (Chrome 120, Firefox 121, etc.)
2. **Console output** (copy/paste all logs)
3. **Network tab** - Screenshot or list of requests
4. **Any red errors** in console
5. **Whether manual API test works** (Step 5)

