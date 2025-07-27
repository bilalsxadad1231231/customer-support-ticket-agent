import React, { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  DocumentArrowUpIcon, 
  CloudArrowUpIcon, 
  CheckCircleIcon, 
  XMarkIcon,
  BookmarkIcon,
  Bars3Icon,
  SparklesIcon
} from '@heroicons/react/24/outline';

function Sidebar({ collapsed, pinned, onPinToggle }) {
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadError, setUploadError] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [fileName, setFileName] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingMessage, setProcessingMessage] = useState('');
  const [completionMessage, setCompletionMessage] = useState('');
  const fileInputRef = useRef(null);

  const categories = [
    { value: 'general', label: 'General' },
    { value: 'technical', label: 'Technical' },
    { value: 'billing', label: 'Billing' },
    { value: 'security', label: 'Security' }
  ];

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    if (rejectedFiles && rejectedFiles.length > 0) {
      setUploadError(true);
      setTimeout(() => setUploadError(false), 3000);
      return;
    }

    if (acceptedFiles && acceptedFiles.length > 0) {
      setFileName(acceptedFiles[0].name);
      setUploadSuccess(true);
      setTimeout(() => setUploadSuccess(false), 3000);
    }
  }, []);

  const handleFileUpload = async () => {
    if (!fileInputRef.current?.files[0] || !selectedCategory) {
      setUploadError(true);
      setTimeout(() => setUploadError(false), 3000);
      return;
    }

    setIsUploading(true);
    setIsProcessing(true);
    setProcessingMessage('Uploading file to server...');
    setUploadError(false);
    setUploadSuccess(false);

    try {
      const formData = new FormData();
      formData.append('files', fileInputRef.current.files[0]);
      formData.append('category', selectedCategory);

      // Step 1: Upload file
      setProcessingMessage('Uploading file to server...');
      const response = await fetch('http://localhost:2024/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          // Step 2: Processing phase
          setProcessingMessage('Processing PDF and indexing documents...');
          
          // Simulate processing time (you can remove this if backend is fast)
          await new Promise(resolve => setTimeout(resolve, 2000));
          
          // Step 3: Completion
          setIsProcessing(false);
          setCompletionMessage(`Successfully processed "${fileName}" and indexed under "${selectedCategory}" category!`);
          setUploadSuccess(true);
          
          // Reset form
          setFileName('');
          setSelectedCategory('');
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
          
          // Clear completion message after 5 seconds
          setTimeout(() => {
            setUploadSuccess(false);
            setCompletionMessage('');
          }, 5000);
          
        } else {
          throw new Error(result.error || 'Upload failed');
        }
      } else {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Upload error:', error);
      setIsProcessing(false);
      setUploadError(true);
      setTimeout(() => setUploadError(false), 3000);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <AnimatePresence mode="wait">
      <motion.aside
        initial={{ width: collapsed ? 64 : 280 }}
        animate={{ width: collapsed ? 64 : 280 }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="bg-white border-r border-gray-200 flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          {!collapsed && (
            <motion.h2 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-lg font-semibold text-gray-900"
            >
              Quick Actions
            </motion.h2>
          )}
          <div className="flex items-center space-x-2">
            <button
              onClick={onPinToggle}
              className="p-1 rounded-md hover:bg-gray-100 transition-colors"
              title={pinned ? "Unpin sidebar" : "Pin sidebar"}
            >
              <BookmarkIcon className={`w-4 h-4 ${pinned ? 'text-accent fill-current' : 'text-gray-400'}`} />
            </button>
          </div>
        </div>

        {/* Content - Only show when not collapsed */}
        {!collapsed && (
          <div className="flex-1 p-4 space-y-6">
            {/* File Upload Section */}
            <div className="space-y-4">
              <motion.h3 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-sm font-medium text-gray-700"
              >
                Upload Documents
              </motion.h3>
              
              {/* Category Selection */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-2"
              >
                <label className="block text-xs font-medium text-gray-700">
                  Category
                </label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  disabled={isUploading || isProcessing}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-accent focus:border-accent disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <option value="">Select a category</option>
                  {categories.map((category) => (
                    <option key={category.value} value={category.value}>
                      {category.label}
                    </option>
                  ))}
                </select>
              </motion.div>

              {/* File Upload Zone */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                  uploadSuccess ? 'border-green-300 bg-green-50' :
                  uploadError ? 'border-red-300 bg-red-50' :
                  isProcessing ? 'border-blue-300 bg-blue-50' :
                  'border-gray-300 hover:border-accent'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  disabled={isUploading || isProcessing}
                  onChange={(e) => {
                    if (e.target.files?.[0]) {
                      setFileName(e.target.files[0].name);
                      onDrop([e.target.files[0]], []);
                    }
                  }}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
                />
                
                <div className="space-y-3">
                  {isProcessing ? (
                    <SparklesIcon className="mx-auto h-8 w-8 text-blue-500 animate-pulse" />
                  ) : (
                    <CloudArrowUpIcon className="mx-auto h-8 w-8 text-gray-400" />
                  )}
                  <div>
                    {isProcessing ? (
                      <p className="text-sm text-blue-600 font-medium">{processingMessage}</p>
                    ) : (
                      <>
                        <p className="text-sm text-gray-600">
                          <span className="font-medium text-accent">Click to upload</span> or drag and drop
                        </p>
                        <p className="text-xs text-gray-500 mt-1">PDF files only</p>
                      </>
                    )}
                  </div>
                  {fileName && !isProcessing && (
                    <p className="text-sm text-gray-600 truncate">{fileName}</p>
                  )}
                </div>
              </motion.div>

              {/* Upload Button */}
              <motion.button
                onClick={handleFileUpload}
                disabled={!fileName || !selectedCategory || isUploading || isProcessing}
                className="w-full btn-primary flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                {isUploading || isProcessing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>{isProcessing ? 'Processing...' : 'Uploading...'}</span>
                  </>
                ) : (
                  <>
                    <DocumentArrowUpIcon className="w-4 h-4" />
                    <span>Upload Document</span>
                  </>
                )}
              </motion.button>

              {/* Processing Status */}
              <AnimatePresence>
                {isProcessing && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="flex items-center space-x-2 text-blue-600 text-sm bg-blue-50 p-3 rounded-lg"
                  >
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    <span>{processingMessage}</span>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Success/Error Messages */}
              <AnimatePresence>
                {uploadSuccess && completionMessage && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="flex items-start space-x-2 text-green-600 text-sm bg-green-50 p-3 rounded-lg"
                  >
                    <CheckCircleIcon className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span>{completionMessage}</span>
                  </motion.div>
                )}
                {uploadError && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="flex items-center space-x-2 text-red-600 text-sm bg-red-50 p-3 rounded-lg"
                  >
                    <XMarkIcon className="w-4 h-4" />
                    <span>Upload failed. Please try again.</span>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        )}
      </motion.aside>
    </AnimatePresence>
  );
}

export default Sidebar; 