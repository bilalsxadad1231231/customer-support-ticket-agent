import { generateUniqueTicketId } from '../utils/ticketUtils';

class AgentService {
  constructor() {
    this.baseUrl = 'http://localhost:2024';
    this.assistantId = 'support_agent';
  }

  // Method to submit ticket to agent
  async submitTicket(ticketData) {
    try {
      const payload = {
        ticket: {
          subject: ticketData.title,
          description: ticketData.description,
          ticket_id: generateUniqueTicketId()
        }
      };

      console.log('Submitting ticket to agent:', payload);
      return payload;

    } catch (error) {
      console.error('Error submitting ticket:', error);
      return {
        success: false,
        error: error.message,
        response: 'Failed to submit ticket to agent'
      };
    }
  }
}

const agentService = new AgentService();
export default agentService; 