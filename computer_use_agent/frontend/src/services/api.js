const API_BASE = "http://localhost:8000/api/v1";
const WS_BASE = "ws://localhost:8000/api/v1";

export const taskAPI = {
  submit: async (goal) => {
    const response = await fetch(`${API_BASE}/tasks`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ goal }),
    });
    if (!response.ok) throw new Error("Failed to submit task");
    return response.json();
  },

  list: async () => {
    const response = await fetch(`${API_BASE}/tasks`);
    if (!response.ok) throw new Error("Failed to fetch tasks list");
    return response.json();
  },

  getDetails: async (taskId) => {
    const response = await fetch(`${API_BASE}/tasks/${taskId}`);
    if (!response.ok) throw new Error("Failed to fetch task details");
    return response.json();
  },

  getAudits: async () => {
    const response = await fetch(`${API_BASE}/audits`);
    if (!response.ok) throw new Error("Failed to fetch audit logs");
    return response.json();
  },

  getWebSocketStream: () => {
    return new WebSocket(`${WS_BASE}/ws/stream`);
  }
};
