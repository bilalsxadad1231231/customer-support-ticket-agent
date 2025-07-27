import React, { useState } from 'react';
import { generateUniqueTicketId, getTicketCounter, resetTicketCounter } from '../../utils/ticketUtils';

function TicketIdTest() {
  const [ticketIds, setTicketIds] = useState([]);

  const generateNewTicketId = () => {
    const newTicketId = generateUniqueTicketId();
    setTicketIds(prev => [...prev, {
      id: newTicketId,
      timestamp: new Date().toLocaleTimeString(),
      counter: getTicketCounter()
    }]);
  };

  const clearTicketIds = () => {
    setTicketIds([]);
    resetTicketCounter();
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold mb-4">Ticket ID Generation Test</h2>
        
        <div className="flex space-x-4 mb-6">
          <button
            onClick={generateNewTicketId}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
          >
            Generate New Ticket ID
          </button>
          <button
            onClick={clearTicketIds}
            className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded"
          >
            Clear All
          </button>
        </div>

        <div className="mb-4">
          <p className="text-sm text-gray-600">
            Current Ticket Counter: <span className="font-bold">{getTicketCounter()}</span>
          </p>
        </div>

        {ticketIds.length > 0 && (
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold mb-3">Generated Ticket IDs:</h3>
            <div className="space-y-2">
              {ticketIds.map((ticket, index) => (
                <div key={index} className="bg-white p-3 rounded border">
                  <div className="flex justify-between items-center">
                    <span className="font-mono text-sm break-all">{ticket.id}</span>
                    <span className="text-xs text-gray-500 ml-2">
                      {ticket.timestamp} (Counter: {ticket.counter})
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {ticketIds.length > 1 && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <h4 className="font-semibold text-yellow-800 mb-2">Uniqueness Check:</h4>
            <p className="text-sm text-yellow-700">
              {ticketIds.length === new Set(ticketIds.map(t => t.id)).size 
                ? '✅ All ticket IDs are unique!' 
                : '❌ Duplicate ticket IDs found!'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default TicketIdTest; 