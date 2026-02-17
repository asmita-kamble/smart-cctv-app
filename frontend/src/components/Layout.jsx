import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Layout = () => {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const isDashboard = location.pathname === '/dashboard' || location.pathname === '/';
  const hasBackground = ['/dashboard', '/', '/cameras', '/alerts', '/activities', '/live-feed'].includes(location.pathname);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className={`min-h-screen ${hasBackground ? 'bg-transparent' : 'bg-gray-50'}`}>
      <nav className={`fixed top-0 left-0 right-0 z-50 shadow-lg border-b border-slate-700 ${hasBackground ? 'bg-slate-800/95 backdrop-blur-md' : 'bg-slate-800'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold text-white">Smart CCTV</h1>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                <Link
                  to="/dashboard"
                  className="border-transparent text-gray-300 hover:border-blue-400 hover:text-white inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors"
                >
                  Dashboard
                </Link>
                <Link
                  to="/cameras"
                  className="border-transparent text-gray-300 hover:border-blue-400 hover:text-white inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors"
                >
                  Cameras
                </Link>
                <Link
                  to="/live-feed"
                  className="border-transparent text-gray-300 hover:border-blue-400 hover:text-white inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors"
                >
                  Live Feed
                </Link>
                <Link
                  to="/alerts"
                  className="border-transparent text-gray-300 hover:border-blue-400 hover:text-white inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors"
                >
                  Alerts
                </Link>
                <Link
                  to="/activities"
                  className="border-transparent text-gray-300 hover:border-blue-400 hover:text-white inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors"
                >
                  Activities
                </Link>
              </div>
            </div>
            <div className="flex items-center">
              <span className="text-sm text-gray-200 mr-4">
                {user?.username} ({user?.role})
              </span>
              <button
                onClick={handleLogout}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className={`max-w-7xl mx-auto py-6 sm:px-6 lg:px-8 pt-24 ${hasBackground ? 'bg-transparent' : ''}`}>
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;

