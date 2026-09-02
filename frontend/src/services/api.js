const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let message = `API request failed: ${response.status}`;

    try {
      const errorData = await response.json();
      message =
        errorData.detail ||
        errorData.message ||
        message;
    } catch {
      // Keep the default error message.
    }

    throw new Error(message);
  }

  return response.json();
}

export const api = {
  health: () => request("/health"),

  runSimulation: (payload) =>
    request("/simulation/run", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getAnalyticsReport: () =>
    request("/analytics/report"),

  getPayments: (params = {}) => {
    const query = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        query.set(key, value);
      }
    });

    const suffix = query.toString()
      ? `?${query.toString()}`
      : "";

    return request(`/payments${suffix}`);
  },

  getPayment: (paymentId) =>
    request(`/payments/${paymentId}`),

  getRecommendations: (paymentId) =>
    request(`/recovery/${paymentId}`),

  getRecovery: (paymentId) =>
    request(`/recovery/${paymentId}`),

  getAdaptiveDecision: (paymentId) =>
  request(`/adaptive-decision/${paymentId}`),

getCounterfactual: (paymentId) =>
  request(`/counterfactual/${paymentId}`),

  approveRecovery: (paymentId) =>
    request(`/recovery/${paymentId}/approve`, {
      method: "POST",
    }),

  executeRecovery: (paymentId) =>
    request(`/recovery/${paymentId}/execute`, {
      method: "POST",
    }),
};