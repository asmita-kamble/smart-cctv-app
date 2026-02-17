import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  // Log component mount
  console.log('Login component rendered');
  console.log('Current email state:', email);
  console.log('Current password length:', password.length);

  const handleSubmit = async (e) => {
    // Log immediately - before anything else
    console.log('=== FORM SUBMIT EVENT FIRED ===');
    console.log('Event type:', e.type);
    console.log('Email value:', email);
    console.log('Password length:', password.length);
    
    e.preventDefault();
    e.stopPropagation();
    
    console.log('=== LOGIN FORM SUBMITTED ===');
    console.log('Email:', email);
    console.log('Password length:', password.length);
    console.log('Email type:', typeof email);
    console.log('Email length:', email?.length);
    
    // Validate inputs before proceeding
    if (!email || !password) {
      console.error('Validation failed - missing email or password');
      setError('Email and password are required');
      return;
    }
    
    if (email.trim() === '' || password.trim() === '') {
      console.error('Validation failed - empty email or password');
      setError('Email and password cannot be empty');
      return;
    }
    
    setError('');
    setLoading(true);
    console.log('Loading state set to true');

    try {
      console.log('Step 1: Calling login function from AuthContext...');
      const result = await login(email, password);
      console.log('Step 2: Login result received:', result);
      console.log('Step 3: Result success?', result.success);
      
      setLoading(false);

      if (result && result.success) {
        console.log('Step 4: Login successful, checking token storage...');
        // Wait a moment to ensure token is stored
        await new Promise(resolve => setTimeout(resolve, 200));
        
        // Check if token was stored
        const token = localStorage.getItem('token');
        const user = localStorage.getItem('user');
        console.log('Step 5: Token check -', token ? 'FOUND' : 'NOT FOUND');
        console.log('Step 6: User check -', user ? 'FOUND' : 'NOT FOUND');
        
        if (token) {
          console.log('Step 7: Token verified, navigating to dashboard...');
          console.log('Token preview:', token.substring(0, 30) + '...');
          // Force a small delay to ensure state updates
          setTimeout(() => {
            navigate('/dashboard', { replace: true });
          }, 100);
        } else {
          console.error('Step 7 ERROR: Token not found after successful login!');
          console.error('LocalStorage contents:', {
            token: localStorage.getItem('token'),
            user: localStorage.getItem('user'),
            allKeys: Object.keys(localStorage),
          });
          setError('Login succeeded but token not stored. Please check console for details.');
        }
      } else {
        console.error('Step 4 ERROR: Login failed');
        console.error('Result:', result);
        const errorMsg = result?.error || 'Login failed - no error message provided';
        console.error('Error message:', errorMsg);
        setError(errorMsg);
      }
    } catch (error) {
      console.error('=== LOGIN EXCEPTION CAUGHT ===');
      console.error('Error type:', error.constructor.name);
      console.error('Error message:', error.message);
      console.error('Error stack:', error.stack);
      console.error('Error response:', error.response);
      console.error('Error response data:', error.response?.data);
      console.error('Error response status:', error.response?.status);
      setLoading(false);
      
      const errorMsg = error.response?.data?.error || 
                      error.response?.data?.message || 
                      error.message || 
                      'Login failed - check console for details';
      console.error('Setting error message:', errorMsg);
      setError(errorMsg);
    }
  };

  return (
    <div 
      className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden"
      style={{
        background: 'linear-gradient(135deg, #0a1628 0%, #1a1f3a 50%, #0f172a 100%)',
      }}
    >
      {/* Wavy pattern overlay */}
      <div 
        className="absolute inset-0 opacity-30"
        style={{
          backgroundImage: `
            radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(59, 130, 246, 0.2) 0%, transparent 50%),
            radial-gradient(circle at 40% 20%, rgba(99, 102, 241, 0.2) 0%, transparent 50%)
          `,
        }}
      />
      {/* Animated wavy lines */}
      <svg className="absolute inset-0 w-full h-full opacity-20" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 320">
        <path fill="rgba(59, 130, 246, 0.3)" fillOpacity="1" d="M0,96L48,112C96,128,192,160,288,160C384,160,480,128,576,122.7C672,117,768,139,864,154.7C960,171,1056,181,1152,165.3C1248,149,1344,107,1392,85.3L1440,64L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z" style={{animation: 'wave 10s ease-in-out infinite'}}></path>
        <path fill="rgba(99, 102, 241, 0.2)" fillOpacity="1" d="M0,192L48,197.3C96,203,192,213,288,197.3C384,181,480,139,576,133.3C672,128,768,160,864,165.3C960,171,1056,149,1152,133.3C1248,117,1344,107,1392,101.3L1440,96L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z" style={{animation: 'wave 15s ease-in-out infinite reverse'}}></path>
      </svg>

      <div className="max-w-md w-full space-y-8 relative z-10">
        {/* Camera Logo */}
        <div className="flex justify-center mb-4">
          <div className="bg-white/10 backdrop-blur-sm rounded-full p-6 border border-white/20">
            <svg className="w-16 h-16 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </div>
        </div>

        {/* Title */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white mb-2">Smart CCTV. Detection</h1>
          <p className="text-sm text-gray-300">Sign in to access your dashboard</p>
        </div>
        <form 
          className="mt-8 space-y-6 bg-white rounded-xl shadow-2xl p-8" 
          onSubmit={(e) => {
            console.log('FORM onSubmit handler called');
            handleSubmit(e);
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              console.log('Enter key pressed in form');
            }
          }}
        >
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Username
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="appearance-none relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-400 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm bg-white"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => {
                  console.log('Email input changed:', e.target.value);
                  setEmail(e.target.value);
                }}
                onBlur={(e) => {
                  console.log('Email input blurred, value:', e.target.value);
                }}
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="appearance-none relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-400 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm bg-white"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => {
                  console.log('Password input changed, length:', e.target.value.length);
                  setPassword(e.target.value);
                }}
                onBlur={(e) => {
                  console.log('Password input blurred, length:', e.target.value.length);
                }}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              onClick={(e) => {
                console.log('BUTTON CLICKED');
                console.log('Button disabled?', loading);
                console.log('Email:', email);
                console.log('Password length:', password.length);
                // Don't prevent default - let form handle it
              }}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-base font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              {loading ? 'Signing in...' : 'Login'}
            </button>
          </div>

          <div className="text-center">
            <Link 
              to="#" 
              className="inline-block px-4 py-2 text-sm font-medium text-blue-600 border border-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
            >
              Forget Password?
            </Link>
          </div>

          <div className="text-center text-sm text-gray-600">
            Don't have an account?{' '}
            <Link to="/register" className="font-medium text-blue-600 hover:text-blue-500 transition-colors">
              Create a new account
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;

