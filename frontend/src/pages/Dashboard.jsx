import { useState, useEffect } from 'react';
import { dashboardService } from '../services/dashboardService';
import { alertService } from '../services/alertService';
import { useAuth } from '../context/AuthContext';
import { authService } from '../services/authService';

const Dashboard = () => {
  const [overview, setOverview] = useState(null);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const auth = useAuth();
  const { isAdmin, user: contextUser } = auth;

  useEffect(() => {
    // Debug: Log authentication state
    const token = authService.getToken();
    const user = authService.getStoredUser();
    console.log('Dashboard useEffect:', {
      isAdmin,
      hasToken: !!token,
      tokenLength: token?.length,
      tokenValue: token ? token.substring(0, 30) + '...' : 'MISSING',
      user,
      userRole: user?.role,
      contextUser: contextUser,
    });

    // Verify token exists before making request
    if (!token) {
      console.error('Dashboard: No token found!');
      setError('No authentication token found. Please login again.');
      setLoading(false);
      return;
    }

    if (isAdmin || (user && user.role === 'admin')) {
      console.log('Dashboard: Loading overview for admin user');
      loadOverview();
    } else {
      setLoading(false);
      if (user && user.role !== 'admin') {
        setError('Admin access required. Your role: ' + user.role);
      } else {
        setError('Admin access required. Unable to determine user role.');
      }
    }
  }, [isAdmin]);

  const loadOverview = async () => {
    try {
      const data = await dashboardService.getOverview();
      setOverview(data);
      
      // Load recent alerts
      const alertsData = await alertService.getAll({ limit: 10 });
      const alerts = Array.isArray(alertsData) ? alertsData : alertsData.alerts || [];
      setRecentAlerts(alerts);
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to load dashboard data';
      setError(errorMessage);
      console.error('Dashboard error:', err.response?.data || err);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (!isAdmin) {
    return (
      <>
        {/* Full-screen background */}
        <div 
          className="fixed inset-0 -z-10"
          style={{
            backgroundImage: `linear-gradient(135deg, rgba(249, 250, 251, 0.90) 0%, rgba(243, 244, 246, 0.93) 100%), 
                             url('https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80')`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundRepeat: 'no-repeat',
            backgroundAttachment: 'fixed'
          }}
        />
        <div className="relative z-10">
          <div className="bg-white/90 backdrop-blur-sm shadow-lg rounded-lg p-6 border border-white/50">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Dashboard</h2>
            <p className="text-gray-600">Admin access required to view dashboard statistics.</p>
          </div>
        </div>
      </>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <>
        {/* Full-screen background */}
        <div 
          className="fixed inset-0 -z-10"
          style={{
            backgroundImage: `linear-gradient(135deg, rgba(249, 250, 251, 0.90) 0%, rgba(243, 244, 246, 0.93) 100%), 
                             url('https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80')`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundRepeat: 'no-repeat',
            backgroundAttachment: 'fixed'
          }}
        />
        <div className="relative z-10">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          <p className="font-semibold">Error loading dashboard:</p>
          <p>{error}</p>
          <p className="text-sm mt-2">
            Status: 401 Unauthorized - Please check:
          </p>
          <ul className="text-sm mt-2 list-disc list-inside">
            <li>Token is stored: {localStorage.getItem('token') ? 'Yes' : 'No'}</li>
            <li>User is authenticated: {isAdmin ? 'Yes (Admin)' : 'No'}</li>
            <li>Check browser console for more details</li>
          </ul>
          <button
            onClick={() => {
              localStorage.removeItem('token');
              localStorage.removeItem('user');
              window.location.href = '/login';
            }}
            className="mt-4 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
          >
            Clear Storage and Re-login
          </button>
        </div>
        </div>
      </>
    );
  }

  return (
    <>
      {/* Full-screen background */}
      <div 
        className="fixed inset-0 -z-10"
        style={{
          backgroundImage: `linear-gradient(135deg, rgba(249, 250, 251, 0.90) 0%, rgba(243, 244, 246, 0.93) 100%), 
                           url('https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
          backgroundAttachment: 'fixed'
        }}
      />
      <div className="relative z-10">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 drop-shadow-sm">Dashboard Overview</h2>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        <div className="bg-white/90 backdrop-blur-sm overflow-hidden shadow-lg rounded-lg border border-white/50 hover:shadow-xl transition-shadow duration-200">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
                  <span className="text-white text-sm font-bold">C</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Cameras</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {overview?.cameras?.total || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white/90 backdrop-blur-sm overflow-hidden shadow-lg rounded-lg border border-white/50 hover:shadow-xl transition-shadow duration-200">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                  <span className="text-white text-sm font-bold">A</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Active Cameras</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {overview?.cameras?.active || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white/90 backdrop-blur-sm overflow-hidden shadow-lg rounded-lg border border-white/50 hover:shadow-xl transition-shadow duration-200">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-red-500 rounded-md flex items-center justify-center">
                  <span className="text-white text-sm font-bold">!</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Pending Alerts</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {overview?.alerts?.pending_count || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white/90 backdrop-blur-sm overflow-hidden shadow-lg rounded-lg border border-white/50 hover:shadow-xl transition-shadow duration-200">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-yellow-500 rounded-md flex items-center justify-center">
                  <span className="text-white text-sm font-bold">E</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Recent Activities</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {overview?.recent_activities_count || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {overview?.alerts?.severity_counts && (
        <div className="bg-white/90 backdrop-blur-sm shadow-lg rounded-lg p-6 mb-6 border border-white/50">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Alert Severity Distribution</h3>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <p className="text-sm text-gray-500">Critical</p>
              <p className="text-2xl font-bold text-red-600">
                {overview.alerts.severity_counts.critical || 0}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">High</p>
              <p className="text-2xl font-bold text-orange-600">
                {overview.alerts.severity_counts.high || 0}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Medium</p>
              <p className="text-2xl font-bold text-yellow-600">
                {overview.alerts.severity_counts.medium || 0}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Low</p>
              <p className="text-2xl font-bold text-blue-600">
                {overview.alerts.severity_counts.low || 0}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Recent Alerts Section */}
      <div className="bg-white/90 backdrop-blur-sm shadow-lg rounded-lg p-6 border border-white/50">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Alerts</h3>
        {recentAlerts.length === 0 ? (
          <p className="text-gray-500 text-center py-4">No alerts found</p>
        ) : (
          <div className="space-y-3">
            {recentAlerts.map((alert) => (
              <div
                key={alert.id}
                className="border-l-4 border-gray-200 pl-4 py-2 hover:bg-gray-50"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(
                          alert.severity
                        )}`}
                      >
                        {alert.severity}
                      </span>
                      <span className="text-sm font-medium text-gray-900">
                        {alert.alert_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{alert.message}</p>
                    {alert.camera_name && (
                      <p className="text-xs text-gray-400 mt-1">Camera: {alert.camera_name}</p>
                    )}
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(alert.created_at).toLocaleString()}
                    </p>
                  </div>
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      alert.status === 'pending'
                        ? 'bg-yellow-100 text-yellow-800'
                        : alert.status === 'resolved'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {alert.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      </div>
    </>
  );
};

export default Dashboard;

