import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authService } from '../services/authService';

const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const { isAuthenticated, isAdmin, loading, user } = useAuth();

  // Also check localStorage directly as a fallback
  const hasToken = authService.isAuthenticated();
  const storedUser = authService.getStoredUser();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Check authentication - use context state OR localStorage as fallback
  const authenticated = isAuthenticated || (hasToken && storedUser);
  
  console.log('ProtectedRoute check:', {
    isAuthenticated,
    hasToken,
    storedUser: !!storedUser,
    user: !!user,
    authenticated,
    pathname: window.location.pathname,
  });
  
  if (!authenticated) {
    console.log('ProtectedRoute: Not authenticated, redirecting to login', {
      isAuthenticated,
      hasToken,
      storedUser,
      user,
      tokenValue: hasToken ? 'EXISTS' : 'MISSING',
    });
    return <Navigate to="/login" replace />;
  }

  // Check admin requirement
  const userRole = user?.role || storedUser?.role;
  if (requireAdmin && userRole !== 'admin') {
    console.log('ProtectedRoute: Admin required but user is not admin', { userRole });
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

export default ProtectedRoute;

