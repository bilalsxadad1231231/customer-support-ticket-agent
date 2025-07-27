/**
 * Utility functions for ticket management
 */

/**
 * Generates a unique ticket ID that combines timestamp, random string, session ID, and counter
 * This ensures each ticket has a unique identifier even when submitted multiple times quickly
 * @returns {string} Unique ticket ID
 */
export const generateUniqueTicketId = () => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substr(2, 9);
  const sessionId = sessionStorage.getItem('sessionId') || Math.random().toString(36).substr(2, 9);
  
  // Get and increment ticket counter for this session
  const ticketCounter = parseInt(sessionStorage.getItem('ticketCounter') || '0') + 1;
  sessionStorage.setItem('ticketCounter', ticketCounter.toString());
  
  return `TICKET-${timestamp}-${random}-${sessionId}-${ticketCounter}`;
};

/**
 * Initializes session ID if it doesn't exist and resets ticket counter
 * This should be called when the app starts
 */
export const initializeSessionId = () => {
  if (!sessionStorage.getItem('sessionId')) {
    sessionStorage.setItem('sessionId', Math.random().toString(36).substr(2, 9));
    // Reset ticket counter for new session
    sessionStorage.setItem('ticketCounter', '0');
  }
};

/**
 * Gets the current session ID
 * @returns {string} Current session ID
 */
export const getSessionId = () => {
  return sessionStorage.getItem('sessionId');
};

/**
 * Gets the current ticket counter
 * @returns {number} Current ticket counter
 */
export const getTicketCounter = () => {
  return parseInt(sessionStorage.getItem('ticketCounter') || '0');
};

/**
 * Resets the ticket counter to 0
 */
export const resetTicketCounter = () => {
  sessionStorage.setItem('ticketCounter', '0');
};

/**
 * Validates if a ticket ID is properly formatted
 * @param {string} ticketId - The ticket ID to validate
 * @returns {boolean} True if valid, false otherwise
 */
export const isValidTicketId = (ticketId) => {
  if (!ticketId || typeof ticketId !== 'string') {
    return false;
  }
  
  // Check if it follows the pattern: TICKET-timestamp-random-sessionId-counter
  const pattern = /^TICKET-\d+-[a-z0-9]{9}-[a-z0-9]{9}-\d+$/;
  return pattern.test(ticketId);
}; 