# Creating Admin User

There are two ways to create an admin user:

## Method 1: Using curl/API (Recommended for Initial Setup)

Since the registration endpoint accepts a `role` parameter, you can create an admin user directly via the API:

```bash
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "username": "admin",
    "password": "Admin123!",
    "role": "admin"
  }'
```

**Note:** Replace `admin@example.com`, `admin`, and `Admin123!` with your desired credentials.

## Method 2: Using Browser Console

You can also create an admin user directly from the browser console:

1. Open your browser's Developer Tools (F12)
2. Go to the Console tab
3. Run this command (adjust the credentials as needed):

```javascript
fetch('http://localhost:5001/api/auth/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'admin@example.com',
    username: 'admin',
    password: 'Admin123!',
    role: 'admin'
  })
})
.then(response => response.json())
.then(data => console.log('Admin created:', data))
.catch(error => console.error('Error:', error));
```

## Method 3: Update Existing User to Admin (via Database)

If you already have a user and want to make them admin, you can update the database directly:

```bash
# Connect to PostgreSQL
psql -U postgres -d smart_cctv

# Update user role to admin
UPDATE users SET role = 'admin' WHERE email = 'your-email@example.com';

# Verify the change
SELECT id, email, username, role FROM users WHERE email = 'your-email@example.com';

# Exit
\q
```

## Verify Admin Access

After creating an admin user:

1. Log out if you're currently logged in
2. Log in with the admin credentials
3. You should now see the Dashboard with statistics (admin-only feature)
4. Check the browser console - you should see your role as "admin"

## Security Note

The registration endpoint currently allows anyone to create an admin user by including `"role": "admin"` in the request. For production, you should:

1. Remove the ability to set role during registration
2. Only allow existing admins to create new admin users
3. Or use a special admin creation endpoint that requires a secret key

