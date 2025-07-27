import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useForm } from 'react-hook-form';
import { motion, AnimatePresence } from 'framer-motion';
import { ExclamationCircleIcon, CheckCircleIcon, DocumentTextIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { generateUniqueTicketId, initializeSessionId } from '../../utils/ticketUtils';

function SubmitTicket() {
  const [charCount, setCharCount] = useState({ title: 0, description: 0 });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [submitError, setSubmitError] = useState(false);
  const [agentResponse, setAgentResponse] = useState('');
  const [isAgentProcessing, setIsAgentProcessing] = useState(false);
  const abortControllerRef = useRef(null);

  // Initialize session ID if not exists
  useEffect(() => {
    initializeSessionId();
  }, []);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isValid },
    reset,
  } = useForm({
    mode: 'onChange',
  });

  const watchedTitle = watch('title', '');
  const watchedDescription = watch('description', '');

  // Character count tracking
  useEffect(() => {
    setCharCount({
      title: watchedTitle.length,
      description: watchedDescription.length,
    });
  }, [watchedTitle, watchedDescription]);

  const onSubmit = useCallback(async (data) => {
    setIsSubmitting(true);
    setSubmitError(false);
    setAgentResponse('');
    setIsAgentProcessing(true);
    abortControllerRef.current = new AbortController();

    try {
      // Build the payload as required with unique ticket ID
      const ticketId = generateUniqueTicketId();
      console.log('Generated unique ticket ID:', ticketId);
      
      const payload = {
        ticket: {
          subject: data.title,
          description: data.description,
          ticket_id: ticketId
        }
      };

      const response = await fetch('http://localhost:2024/runs/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          thread_id: null,
          assistant_id: 'support_agent',
          input: payload,
          stream_mode: ["values"]
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Handle streaming response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.trim() && line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              console.log('Streamed data:', data);
              if (data.data && data.data.final_response) {
                setAgentResponse(data.data.final_response);
                console.log('final_response (nested):', data.data.final_response);
              } else if (data.final_response) {
                setAgentResponse(data.final_response);
                console.log('final_response (top-level):', data.final_response);
              } else if (data.data && typeof data.data === 'string') {
                setAgentResponse(data.data);
              }
            } catch (e) {
              // ignore parse errors for non-JSON lines
            }
          }
        }
      }

      setSubmitSuccess(true);
      reset();
      setTimeout(() => setSubmitSuccess(false), 5000);
    } catch (error) {
      if (error.name !== 'AbortError') {
        setSubmitError(true);
        setTimeout(() => setSubmitError(false), 3000);
      }
    } finally {
      setIsSubmitting(false);
      setIsAgentProcessing(false);
    }
  }, [reset]);

  // Handle cancel
  const handleCancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsAgentProcessing(false);
    setAgentResponse('');
  }, []);

  return (
    <div className="max-w-2xl mx-auto">
      <motion.div 
        className="card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="flex items-center space-x-3 mb-6">
          <DocumentTextIcon className="w-8 h-8 text-accent" />
          <h2 className="text-2xl font-semibold text-primary">Submit New Ticket</h2>
        </div>
        
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Title Field with Character Counter */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
              Ticket Title <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <input
                type="text"
                id="title"
                {...register('title', {
                  required: 'Title is required',
                  minLength: {
                    value: 5,
                    message: 'Title must be at least 5 characters',
                  },
                  maxLength: {
                    value: 100,
                    message: 'Title cannot exceed 100 characters',
                  },
                })}
                className={`input-field pr-12 ${errors.title ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 'focus:border-accent focus:ring-accent'}`}
                placeholder="Brief description of your issue..."
                aria-describedby="title-error title-counter"
              />
              <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                {errors.title ? (
                  <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
                ) : charCount.title > 0 ? (
                  <CheckCircleIcon className="h-5 w-5 text-green-500" />
                ) : null}
              </div>
              {/* Character counter */}
              <div className="absolute -bottom-6 right-0 text-xs text-gray-500">
                {charCount.title}/100
              </div>
            </div>
            <AnimatePresence>
              {errors.title && (
                <motion.p
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="mt-2 text-sm text-red-500 flex items-center"
                  id="title-error"
                >
                  <ExclamationCircleIcon className="w-4 h-4 mr-1" />
                  {errors.title.message}
                </motion.p>
              )}
            </AnimatePresence>
          </div>

          {/* Description Field with Auto-expanding Textarea */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Detailed Description <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <textarea
                id="description"
                {...register('description', {
                  required: 'Description is required',
                  minLength: {
                    value: 20,
                    message: 'Description must be at least 20 characters',
                  },
                  maxLength: {
                    value: 1000,
                    message: 'Description cannot exceed 1000 characters',
                  },
                })}
                className={`input-field resize-none pr-12 ${errors.description ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 'focus:border-accent focus:ring-accent'}`}
                placeholder="Please provide detailed information about your request..."
                rows={Math.max(4, Math.ceil(watchedDescription.length / 50))}
                style={{ minHeight: '120px' }}
                aria-describedby="description-error description-counter"
              />
              <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                {errors.description ? (
                  <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
                ) : charCount.description > 0 ? (
                  <CheckCircleIcon className="h-5 w-5 text-green-500" />
                ) : null}
              </div>
              {/* Character counter */}
              <div className="absolute -bottom-6 right-0 text-xs text-gray-500">
                {charCount.description}/1000
              </div>
            </div>
            <AnimatePresence>
              {errors.description && (
                <motion.p
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="mt-2 text-sm text-red-500 flex items-center"
                  id="description-error"
                >
                  <ExclamationCircleIcon className="w-4 h-4 mr-1" />
                  {errors.description.message}
                </motion.p>
              )}
            </AnimatePresence>
          </div>

          {/* Submit Buttons with Enhanced Feedback */}
          <div className="flex space-x-4 pt-6">
            <motion.button
              type="submit"
              disabled={isSubmitting || !isValid}
              className="btn-primary flex-1 flex justify-center items-center"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {isSubmitting ? (
                <>
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Submitting...
                </>
              ) : (
                'Submit Ticket'
              )}
            </motion.button>
            <motion.button 
              type="button" 
              className="btn-secondary"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleCancel}
            >
              Cancel
            </motion.button>
          </div>
        </form>

        {/* Agent Processing Status */}
        <AnimatePresence>
          {isAgentProcessing && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-center"
            >
              <SparklesIcon className="w-5 h-5 text-blue-500 mr-2 animate-pulse" />
              <span className="text-blue-800 font-medium">AI Agent is processing your request...</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Agent Response */}
        <AnimatePresence>
          {agentResponse && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg"
            >
              <div className="flex items-center mb-3">
                <SparklesIcon className="w-5 h-5 text-green-500 mr-2" />
                <h3 className="text-green-800 font-medium">AI Agent Response</h3>
              </div>
              <div className="text-green-700 whitespace-pre-wrap">
                {agentResponse}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Success/Error Feedback */}
        <AnimatePresence>
          {submitSuccess && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center"
            >
              <CheckCircleIcon className="w-5 h-5 text-green-500 mr-2" />
              <span className="text-green-800 font-medium">Ticket submitted successfully!</span>
            </motion.div>
          )}
          {submitError && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center"
            >
              <ExclamationCircleIcon className="w-5 h-5 text-red-500 mr-2" />
              <span className="text-red-800 font-medium">Failed to submit ticket. Please try again.</span>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}

export default SubmitTicket; 