import React, { createContext, useState, useEffect, useContext } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const storedUser = authService.getStoredUser();
    const token = authService.getToken();
    if (storedUser && token) {
      setUser(storedUser);
      // Verify token is still valid by fetching current user
      authService.getCurrentUser()
        .then((response) => {
          const currentUser = response.user || response;
          setUser(currentUser);
          localStorage.setItem('user', JSON.stringify(currentUser));
        })
        .catch((err) => {
          console.warn('Token validation failed:', err);
          // Token invalid, clear storage
          authService.logout();
          setUser(null);
        });
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      console.log('=== AuthContext.login START ===');
      console.log('Email:', email);
      console.log('Calling authService.login...');
      
      const data = await authService.login(email, password);
      console.log('=== authService.login completed ===');
      console.log('Received data:', data);
      console.log('Data type:', typeof data);
      console.log('Data keys:', data ? Object.keys(data) : 'null/undefined');
      
      // Handle different response formats
      const token = data?.access_token || data?.token;
      const user = data?.user || (data?.id ? data : null);
      
      console.log('Extracted token:', token ? `EXISTS (${token.length} chars)` : 'MISSING');
      console.log('Extracted user:', user);
      console.log('User role:', user?.role);
      
      if (token) {
        // Token is already stored by authService.login
        // Now update the user state
        if (user) {
          console.log('Setting user state with:', user);
          setUser(user);
          console.log('✓ User state updated');
        } else {
          // Try to get user from stored data
          const storedUser = authService.getStoredUser();
          if (storedUser) {
            console.log('Using user from storage:', storedUser);
            setUser(storedUser);
          } else {
            console.warn('⚠ No user in response or storage');
          }
        }
        console.log('=== AuthContext.login SUCCESS ===');
        return { success: true, data };
      } else {
        console.error('=== AuthContext.login ERROR ===');
        console.error('No token in login response!');
        console.error('Full data:', JSON.stringify(data, null, 2));
        return {
          success: false,
          error: 'Invalid response from server - no token received',
        };
      }
    } catch (error) {
      console.error('=== AuthContext.login EXCEPTION ===');
      console.error('Error type:', error.constructor.name);
      console.error('Error message:', error.message);
      console.error('Error stack:', error.stack);
      console.error('Error response:', error.response);
      console.error('Error response data:', error.response?.data);
      console.error('Error response status:', error.response?.status);
      
      const errorMsg = error.response?.data?.error || 
                      error.response?.data?.message || 
                      error.message || 
                      'Login failed';
      console.error('Returning error:', errorMsg);
      return {
        success: false,
        error: errorMsg,
      };
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  const register = async (userData) => {
    try {
      console.log('AuthContext register - calling authService with:', userData);
      const data = await authService.register(userData);
      console.log('AuthContext register - received data:', data);
      return { success: true, data };
    } catch (error) {
      console.error('AuthContext register error:', error);
      const errorMsg = error.response?.data?.error || 
                     error.response?.data?.message || 
                     error.message || 
                     'Registration failed';
      return {
        success: false,
        error: errorMsg,
      };
    }
  };

  const value = {
    user,
    loading,
    login,
    logout,
    register,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

