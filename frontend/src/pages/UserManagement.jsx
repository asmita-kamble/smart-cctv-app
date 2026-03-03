import { useState, useEffect } from 'react';
import { userManagementService } from '../services/userManagementService';
import { useAuth } from '../context/AuthContext';

const UserManagement = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteUsername, setInviteUsername] = useState('');
  const [inviteRole, setInviteRole] = useState('user');
  const [inviteLoading, setInviteLoading] = useState(false);
  const [inviteSuccess, setInviteSuccess] = useState('');
  const [inviteError, setInviteError] = useState('');
  const [actionLoading, setActionLoading] = useState(null);

  const loadUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await userManagementService.listUsers({ limit: 200, offset: 0 });
      setUsers(data.users || []);
      setTotal(data.total ?? 0);
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleInvite = async (e) => {
    e.preventDefault();
    setInviteError('');
    setInviteSuccess('');
    if (!inviteEmail.trim() || !inviteUsername.trim()) {
      setInviteError('Email and username are required');
      return;
    }
    setInviteLoading(true);
    try {
      await userManagementService.inviteUser({
        email: inviteEmail.trim(),
        username: inviteUsername.trim(),
        role: inviteRole,
      });
      setInviteSuccess('Invitation sent. The user will receive an email to set their password.');
      setInviteEmail('');
      setInviteUsername('');
      setInviteRole('user');
      loadUsers();
    } catch (err) {
      setInviteError(err.response?.data?.error || err.message || 'Failed to send invite');
    } finally {
      setInviteLoading(false);
    }
  };

  const handleDeactivate = async (userId) => {
    setActionLoading(userId);
    try {
      await userManagementService.deactivateUser(userId);
      loadUsers();
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to deactivate');
    } finally {
      setActionLoading(null);
    }
  };

  const handleActivate = async (userId) => {
    setActionLoading(userId);
    try {
      await userManagementService.reactivateUser(userId);
      loadUsers();
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to reactivate');
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">User Management</h2>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Invite form */}
      <div className="bg-white/90 backdrop-blur-sm shadow-lg rounded-lg p-6 border border-white/50">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Invite User or Admin</h3>
        <form onSubmit={handleInvite} className="space-y-4 max-w-xl">
          {inviteError && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
              {inviteError}
            </div>
          )}
          {inviteSuccess && (
            <div className="bg-green-50 border border-green-200 text-green-700 px-3 py-2 rounded text-sm">
              {inviteSuccess}
            </div>
          )}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="invite-email" className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                id="invite-email"
                type="email"
                required
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="user@example.com"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="invite-username" className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <input
                id="invite-username"
                type="text"
                required
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="johndoe"
                value={inviteUsername}
                onChange={(e) => setInviteUsername(e.target.value)}
              />
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <label htmlFor="invite-role" className="block text-sm font-medium text-gray-700 mb-1">
                Role
              </label>
              <select
                id="invite-role"
                className="block px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
              >
                <option value="user">User</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div className="pt-6">
              <button
                type="submit"
                disabled={inviteLoading}
                className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {inviteLoading ? 'Sending...' : 'Send Invite'}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Users table */}
      <div className="bg-white/90 backdrop-blur-sm shadow-lg rounded-lg border border-white/50 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200 sm:px-6">
          <h3 className="text-lg font-medium text-gray-900">All Users ({total})</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Username
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                    No users found.
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">{u.username}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{u.email}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                          u.role === 'admin' ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {u.role}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                          u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {u.is_active ? 'Active' : 'Deactivated'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                    </td>
                    <td className="px-4 py-3 text-right text-sm">
                      {u.id === currentUser?.id ? (
                        <span className="text-gray-400">(you)</span>
                      ) : u.is_active ? (
                        <button
                          onClick={() => handleDeactivate(u.id)}
                          disabled={actionLoading === u.id}
                          className="text-red-600 hover:text-red-800 font-medium disabled:opacity-50"
                        >
                          {actionLoading === u.id ? '...' : 'Deactivate'}
                        </button>
                      ) : (
                        <button
                          onClick={() => handleActivate(u.id)}
                          disabled={actionLoading === u.id}
                          className="text-green-600 hover:text-green-800 font-medium disabled:opacity-50"
                        >
                          {actionLoading === u.id ? '...' : 'Activate'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default UserManagement;
