import { useState, useEffect, useRef } from 'react';
import { cameraService } from '../services/cameraService';
import { videoService } from '../services/videoService';

const Cameras = () => {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingCamera, setEditingCamera] = useState(null);
  const [uploading, setUploading] = useState({});
  const [uploadModal, setUploadModal] = useState(null);
  const videoInputRef = useRef(null);
  const imageInputRef = useRef(null);
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    ip: '',
    rtspUsername: '',
    rtspPassword: '',
    rtspPath: '',
    isRestrictedZone: false,
    status: 'active',
  });
  const [allowedPersonImages, setAllowedPersonImages] = useState([]);
  const [existingAllowedPersons, setExistingAllowedPersons] = useState([]);
  const [viewingImage, setViewingImage] = useState(null);
  const allowedPersonInputRef = useRef(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  useEffect(() => {
    loadCameras();
  }, []);


  const loadCameras = async () => {
    try {
      const data = await cameraService.getAll();
      setCameras(Array.isArray(data) ? data : data.cameras || []);
    } catch (err) {
      setError('Failed to load cameras');
    } finally {
      setLoading(false);
    }
  };

  const checkDuplicateName = (name, excludeId = null) => {
    const trimmedName = name.trim().toLowerCase();
    return cameras.some(
      (camera) =>
        camera.name.trim().toLowerCase() === trimmedName &&
        (!excludeId || camera.id !== excludeId)
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate unique name
    const trimmedName = formData.name.trim();
    if (!trimmedName) {
      setError('Camera name is required');
      return;
    }
    
    if (editingCamera) {
      // For edit: check if name is duplicate (excluding current camera)
      if (checkDuplicateName(trimmedName, editingCamera.id)) {
        setError('Camera name already exists. Please choose a different name.');
        return;
      }
    } else {
      // For create: check if name is duplicate
      if (checkDuplicateName(trimmedName)) {
        setError('Camera name already exists. Please choose a different name.');
        return;
      }
    }
    
    try {
      if (editingCamera) {
        // Update existing camera
        await cameraService.update(editingCamera.id, formData);
        
        // Upload new allowed person images if any
        let successCount = 0;
        if (allowedPersonImages.length > 0) {
          for (const image of allowedPersonImages) {
            try {
              await cameraService.uploadAllowedPersonImage(editingCamera.id, image);
              successCount++;
            } catch (err) {
              console.error('Failed to upload allowed person image:', err);
            }
          }
        }
        
        setShowModal(false);
        setEditingCamera(null);
        setFormData({ name: '', location: '', ip: '', rtspUsername: '', rtspPassword: '', rtspPath: '', isRestrictedZone: false, status: 'active' });
        setAllowedPersonImages([]);
        setExistingAllowedPersons([]);
        if (allowedPersonInputRef.current) {
          allowedPersonInputRef.current.value = '';
        }
        loadCameras();
        setSuccess('Camera updated successfully');
      } else {
        // Create new camera
        const cameraResponse = await cameraService.create(formData);
        const cameraId = cameraResponse?.camera?.id;
        
        if (!cameraId) {
          setError('Failed to create camera: Invalid response');
          return;
        }
        
        // Upload allowed person images if any
        let successCount = 0;
        if (allowedPersonImages.length > 0) {
          for (const image of allowedPersonImages) {
            try {
              await cameraService.uploadAllowedPersonImage(cameraId, image);
              successCount++;
            } catch (err) {
              console.error('Failed to upload allowed person image:', err);
            }
          }
          if (successCount < allowedPersonImages.length) {
            setError(`Camera created but ${allowedPersonImages.length - successCount} image(s) failed to upload`);
          }
        }
        
        setShowModal(false);
        setFormData({ name: '', location: '', ip: '', rtspUsername: '', rtspPassword: '', rtspPath: '', isRestrictedZone: false, status: 'active' });
        setAllowedPersonImages([]);
        if (allowedPersonInputRef.current) {
          allowedPersonInputRef.current.value = '';
        }
        loadCameras();
        if (allowedPersonImages.length === 0 || successCount === allowedPersonImages.length) {
          setSuccess('Camera created successfully');
        }
      }
    } catch (err) {
      setError(err.response?.data?.error || (editingCamera ? 'Failed to update camera' : 'Failed to create camera'));
    }
  };

  const handleEdit = async (camera) => {
    try {
      // Load camera details
      const cameraDetails = await cameraService.getById(camera.id);
      const cameraData = cameraDetails.camera || cameraDetails;
      
      // Set form data
      setFormData({
        name: cameraData.name || '',
        location: cameraData.location || '',
        ip: cameraData.ip_address || '',
        rtspUsername: cameraData.rtsp_username || '',
        rtspPassword: cameraData.rtsp_password || '',
        rtspPath: cameraData.rtsp_path || '',
        isRestrictedZone: cameraData.is_restricted_zone || false,
        status: cameraData.status || 'active',
      });
      
      // Load existing allowed persons
      try {
        const allowedPersonsData = await cameraService.getAllowedPersons(camera.id);
        const persons = allowedPersonsData.allowed_persons || [];
        setExistingAllowedPersons(persons);
        
        // Pre-load images for existing allowed persons
        persons.forEach((person) => {
          getImageUrl(camera.id, person.id);
        });
      } catch (err) {
        console.error('Failed to load allowed persons:', err);
        setExistingAllowedPersons([]);
      }
      
      setEditingCamera(camera);
      setAllowedPersonImages([]);
      setShowModal(true);
    } catch (err) {
      setError('Failed to load camera details');
    }
  };

  const handleDeleteAllowedPerson = async (cameraId, allowedPersonId) => {
    if (window.confirm('Are you sure you want to delete this allowed person image?')) {
      try {
        await cameraService.deleteAllowedPerson(cameraId, allowedPersonId);
        setExistingAllowedPersons(existingAllowedPersons.filter(ap => ap.id !== allowedPersonId));
        setSuccess('Allowed person image deleted successfully');
      } catch (err) {
        setError('Failed to delete allowed person image');
      }
    }
  };

  const openAddModal = () => {
    setEditingCamera(null);
    setFormData({ name: '', location: '', ip: '', rtspUsername: '', rtspPassword: '', rtspPath: '', isRestrictedZone: false, status: 'active' });
    setAllowedPersonImages([]);
    setExistingAllowedPersons([]);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingCamera(null);
    setFormData({ name: '', location: '', ip: '', rtspUsername: '', rtspPassword: '', rtspPath: '', isRestrictedZone: false, status: 'active' });
    setAllowedPersonImages([]);
    setExistingAllowedPersons([]);
    if (allowedPersonInputRef.current) {
      allowedPersonInputRef.current.value = '';
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this camera?')) {
      try {
        await cameraService.delete(id);
        loadCameras();
      } catch (err) {
        setError('Failed to delete camera');
      }
    }
  };

  const handleVideoUpload = async (cameraId, file) => {
    if (!file) return;
    
    setUploading({ ...uploading, [cameraId]: 'video' });
    setError('');
    setSuccess('');
    
    try {
      const result = await videoService.upload(file, cameraId);
      setSuccess(`Video uploaded and processed successfully! Alerts created: ${result.results?.alerts_created || 0}`);
      setUploadModal(null);
      // Reload cameras to show updated data
      setTimeout(() => {
        setSuccess('');
      }, 5000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload video');
    } finally {
      setUploading({ ...uploading, [cameraId]: null });
    }
  };

  const handleImageUpload = async (cameraId, file) => {
    if (!file) return;
    
    setUploading({ ...uploading, [cameraId]: 'image' });
    setError('');
    setSuccess('');
    
    try {
      const result = await videoService.uploadImage(file, cameraId);
      setSuccess(`Image uploaded and processed successfully! Alerts created: ${result.results?.alerts_created || 0}`);
      setUploadModal(null);
      // Reload cameras to show updated data
      setTimeout(() => {
        setSuccess('');
      }, 5000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload image');
    } finally {
      setUploading({ ...uploading, [cameraId]: null });
    }
  };

  const openUploadModal = (cameraId) => {
    setUploadModal(cameraId);
  };

  const closeUploadModal = () => {
    setUploadModal(null);
    if (videoInputRef.current) videoInputRef.current.value = '';
    if (imageInputRef.current) imageInputRef.current.value = '';
  };

  const handleAllowedPersonImageChange = (e) => {
    const files = Array.from(e.target.files);
    setAllowedPersonImages([...allowedPersonImages, ...files]);
  };

  const removeAllowedPersonImage = (index) => {
    setAllowedPersonImages(allowedPersonImages.filter((_, i) => i !== index));
  };

  const [imageBlobs, setImageBlobs] = useState({});

  const getImageUrl = async (cameraId, allowedPersonId) => {
    // Check if we already have a blob URL for this image
    const cacheKey = `${cameraId}_${allowedPersonId}`;
    if (imageBlobs[cacheKey]) {
      return imageBlobs[cacheKey];
    }

    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001/api';
      const token = localStorage.getItem('token');
      
      const response = await fetch(
        `${API_BASE_URL}/cameras/${cameraId}/allowed-persons/${allowedPersonId}/image`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to load image');
      }

      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      
      // Cache the blob URL
      setImageBlobs(prev => ({ ...prev, [cacheKey]: blobUrl }));
      
      return blobUrl;
    } catch (error) {
      console.error('Error loading image:', error);
      return null;
    }
  };

  const handleViewImage = async (cameraId, allowedPersonId, name) => {
    const imageUrl = await getImageUrl(cameraId, allowedPersonId);
    if (imageUrl) {
      setViewingImage({ url: imageUrl, name: name || 'Image' });
    } else {
      setError('Failed to load image');
    }
  };

  const closeImageView = () => {
    setViewingImage(null);
  };

  // Filter cameras based on search query
  const filteredCameras = cameras.filter((camera) => {
    const query = searchQuery.toLowerCase();
    return (
      camera.name?.toLowerCase().includes(query) ||
      camera.location?.toLowerCase().includes(query) ||
      camera.ip_address?.toLowerCase().includes(query) ||
      camera.status?.toLowerCase().includes(query)
    );
  });

  // Pagination calculations
  const totalPages = Math.ceil(filteredCameras.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedCameras = filteredCameras.slice(startIndex, endIndex);

  // Reset to first page when search or itemsPerPage changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, itemsPerPage]);

  const handlePageChange = (page) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
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
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 drop-shadow-sm">Cameras</h2>
        <button
          onClick={openAddModal}
          className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md text-sm font-medium"
        >
          Add Camera
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-4">
          {success}
        </div>
      )}

      {/* Search Bar and Items Per Page */}
      <div className="mb-4 flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            placeholder="Search cameras by name, location, IP address, or status..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
          />
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="itemsPerPage" className="text-sm text-gray-700 whitespace-nowrap">
            Items per page:
          </label>
          <select
            id="itemsPerPage"
            value={itemsPerPage}
            onChange={(e) => setItemsPerPage(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md bg-white text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="5">5</option>
            <option value="10">10</option>
            <option value="25">25</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
        </div>
      </div>
      {searchQuery && (
        <p className="mb-4 text-sm text-gray-600">
          Showing {filteredCameras.length} of {cameras.length} cameras
        </p>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
          <div className="relative mx-auto p-5 border w-full max-w-4xl shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-gray-900 mb-4">
              {editingCamera ? 'Edit Camera' : 'Add New Camera'}
            </h3>
            <form onSubmit={handleSubmit}>
              {/* Two Column Layout */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                {/* Left Column */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                    <input
                      type="text"
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                      value={formData.name}
                      onChange={(e) => {
                        setFormData({ ...formData, name: e.target.value });
                        // Clear error when user starts typing
                        if (error && error.includes('name already exists')) {
                          setError('');
                        }
                      }}
                      placeholder="Enter unique camera name"
                    />
                    {formData.name && checkDuplicateName(
                      formData.name,
                      editingCamera?.id || null
                    ) && (
                      <p className="mt-1 text-sm text-red-600">
                        This camera name already exists. Please choose a different name.
                      </p>
                    )}
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Location *</label>
                    <input
                      type="text"
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                      value={formData.location}
                      onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">IP Address</label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="192.168.1.100"
                      value={formData.ip}
                      onChange={(e) => setFormData({ ...formData, ip: e.target.value })}
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                    <select
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                      value={formData.status}
                      onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    >
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        className="mr-2 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        checked={formData.isRestrictedZone}
                        onChange={(e) => setFormData({ ...formData, isRestrictedZone: e.target.checked })}
                      />
                      <span className="text-sm font-medium text-gray-700">Restricted Zone (ON/OFF)</span>
                    </label>
                  </div>
                </div>
                
                {/* Right Column - RTSP Configuration */}
                <div>
                  <div className="p-3 bg-gray-50 rounded-md border border-gray-200 h-full">
                    <h4 className="text-sm font-semibold text-gray-700 mb-3">RTSP Configuration (Optional)</h4>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">RTSP Username</label>
                        <input
                          type="text"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="admin"
                          value={formData.rtspUsername}
                          onChange={(e) => setFormData({ ...formData, rtspUsername: e.target.value })}
                        />
                        <p className="mt-1 text-xs text-gray-500">Leave empty if no authentication</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">RTSP Password</label>
                        <input
                          type="password"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="password"
                          value={formData.rtspPassword}
                          onChange={(e) => setFormData({ ...formData, rtspPassword: e.target.value })}
                        />
                        <p className="mt-1 text-xs text-gray-500">Leave empty if no authentication</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">RTSP Path</label>
                        <input
                          type="text"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="/stream1"
                          value={formData.rtspPath}
                          onChange={(e) => setFormData({ ...formData, rtspPath: e.target.value })}
                        />
                        <p className="mt-1 text-xs text-gray-500">Default: /stream1</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Allowed Persons - Full Width */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Allowed Persons Images {editingCamera ? '(Add New)' : '(Multiple)'}
                </label>
                <input
                  ref={allowedPersonInputRef}
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handleAllowedPersonImageChange}
                  className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
                {allowedPersonImages.length > 0 && (
                  <div className="mt-2 grid grid-cols-3 gap-2">
                    {allowedPersonImages.map((image, index) => (
                      <div key={index} className="relative group bg-gray-50 rounded border border-gray-200 overflow-hidden">
                        <img
                          src={URL.createObjectURL(image)}
                          alt={image.name}
                          className="w-full h-24 object-cover cursor-pointer"
                          onClick={() => setViewingImage({ url: URL.createObjectURL(image), name: image.name })}
                        />
                        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-opacity flex items-center justify-center">
                          <button
                            type="button"
                            onClick={() => setViewingImage({ url: URL.createObjectURL(image), name: image.name })}
                            className="opacity-0 group-hover:opacity-100 bg-blue-600 text-white px-2 py-1 rounded text-xs hover:bg-blue-700 transition-opacity mr-1"
                          >
                            View
                          </button>
                          <button
                            type="button"
                            onClick={() => removeAllowedPersonImage(index)}
                            className="opacity-0 group-hover:opacity-100 bg-red-600 text-white px-2 py-1 rounded text-xs hover:bg-red-700 transition-opacity"
                          >
                            Remove
                          </button>
                        </div>
                        <p className="text-xs text-gray-600 truncate px-1 py-0.5 bg-white bg-opacity-75">
                          {image.name}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
                {editingCamera && existingAllowedPersons.length > 0 && (
                  <div className="mt-3">
                    <p className="text-sm font-medium text-gray-700 mb-2">Existing Allowed Persons:</p>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {existingAllowedPersons.map((person) => {
                        const imageName = person.name || `Image ${person.id}`;
                        const fileName = person.image_path ? person.image_path.split('/').pop() : `image_${person.id}`;
                        
                        return (
                          <div key={person.id} className="flex items-center justify-between bg-gray-50 p-2 rounded border border-gray-200">
                            <span className="text-sm text-gray-700 truncate flex-1" title={imageName}>
                              {imageName}
                            </span>
                            <div className="flex items-center gap-2 ml-2">
                              <button
                                type="button"
                                onClick={() => handleViewImage(editingCamera.id, person.id, imageName)}
                                className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-xs font-medium"
                              >
                                View
                              </button>
                              <button
                                type="button"
                                onClick={() => handleDeleteAllowedPerson(editingCamera.id, person.id)}
                                className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-xs font-medium"
                              >
                                Delete
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700"
                >
                  {editingCamera ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="bg-white/90 backdrop-blur-sm shadow-lg overflow-hidden sm:rounded-md border border-white/50">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  No.
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Location
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  IP Address
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Restricted Zone
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paginatedCameras.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-4 text-center text-gray-500">
                    {searchQuery ? 'No cameras match your search' : 'No cameras found'}
                  </td>
                </tr>
              ) : (
                paginatedCameras.map((camera, index) => {
                  const rowNumber = startIndex + index + 1;
                  return (
                  <tr key={camera.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{rowNumber}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{camera.name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{camera.location}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{camera.ip_address || '-'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          camera.status === 'active'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {camera.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {camera.is_restricted_zone ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          Yes
                        </span>
                      ) : (
                        <span className="text-sm text-gray-400">No</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => openUploadModal(camera.id)}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-md text-xs font-medium"
                          disabled={uploading[camera.id]}
                        >
                          {uploading[camera.id] ? 'Uploading...' : 'Upload'}
                        </button>
                        <button
                          onClick={() => handleEdit(camera)}
                          className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded-md text-xs font-medium"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(camera.id)}
                          className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-md text-xs font-medium"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {filteredCameras.length > 0 && (
        <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6 mt-4 rounded-md shadow">
          <div className="flex-1 flex justify-between sm:hidden">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className={`relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md ${
                currentPage === 1
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              Previous
            </button>
            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className={`ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md ${
                currentPage === totalPages
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              Next
            </button>
          </div>
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Showing <span className="font-medium">{startIndex + 1}</span> to{' '}
                <span className="font-medium">{Math.min(endIndex, filteredCameras.length)}</span> of{' '}
                <span className="font-medium">{filteredCameras.length}</span> results
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className={`relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium ${
                    currentPage === 1
                      ? 'text-gray-300 cursor-not-allowed'
                      : 'text-gray-500 hover:bg-gray-50'
                  }`}
                >
                  <span className="sr-only">Previous</span>
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </button>
                {[...Array(totalPages)].map((_, index) => {
                  const page = index + 1;
                  // Show first page, last page, current page, and pages around current
                  if (
                    page === 1 ||
                    page === totalPages ||
                    (page >= currentPage - 1 && page <= currentPage + 1)
                  ) {
                    return (
                      <button
                        key={page}
                        onClick={() => handlePageChange(page)}
                        className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                          currentPage === page
                            ? 'z-10 bg-primary-50 border-primary-500 text-primary-600'
                            : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                        }`}
                      >
                        {page}
                      </button>
                    );
                  } else if (page === currentPage - 2 || page === currentPage + 2) {
                    return (
                      <span
                        key={page}
                        className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700"
                      >
                        ...
                      </span>
                    );
                  }
                  return null;
                })}
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className={`relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium ${
                    currentPage === totalPages
                      ? 'text-gray-300 cursor-not-allowed'
                      : 'text-gray-500 hover:bg-gray-50'
                  }`}
                >
                  <span className="sr-only">Next</span>
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                  </svg>
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {uploadModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Upload Media</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload Video (MP4, AVI, MOV, MKV)
                </label>
                <input
                  ref={videoInputRef}
                  type="file"
                  accept="video/*"
                  onChange={(e) => {
                    const file = e.target.files[0];
                    if (file) {
                      handleVideoUpload(uploadModal, file);
                    }
                  }}
                  className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload Image (JPG, PNG, GIF)
                </label>
                <input
                  ref={imageInputRef}
                  type="file"
                  accept="image/*"
                  onChange={(e) => {
                    const file = e.target.files[0];
                    if (file) {
                      handleImageUpload(uploadModal, file);
                    }
                  }}
                  className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
              </div>
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={closeUploadModal}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Image View Modal */}
      {viewingImage && (
        <div className="fixed inset-0 bg-black bg-opacity-75 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
          <div className="relative max-w-4xl max-h-[90vh] m-4">
            <button
              onClick={closeImageView}
              className="absolute top-2 right-2 bg-white bg-opacity-80 hover:bg-opacity-100 text-gray-800 rounded-full p-2 z-10"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <div className="bg-white rounded-lg overflow-hidden">
              <div className="p-4 border-b">
                <h3 className="text-lg font-semibold text-gray-900">{viewingImage.name}</h3>
              </div>
              <div className="p-4">
                <img
                  src={viewingImage.url}
                  alt={viewingImage.name}
                  className="max-w-full max-h-[70vh] mx-auto object-contain"
                  onError={(e) => {
                    e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect width="400" height="300" fill="%23ddd"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999"%3EImage not found%3C/text%3E%3C/svg%3E';
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      )}
      </div>
    </>
  );
};

export default Cameras;

