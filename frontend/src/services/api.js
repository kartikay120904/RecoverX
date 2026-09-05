const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

async function request(endpoint, options = {}) {
  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    }
  );

  if (!response.ok) {
    let message = `API request failed: ${response.status}`;

    try {
      const errorData = await response.json();

      message =
        errorData.detail ||
        errorData.message ||
        message;
    } catch {
      // Keep default error message.
    }

    throw new Error(message);
  }

  return response.json();
}

export const api = {
  health: () =>
    request("/health"),

  runSimulation: (payload = {}) =>
    request("/simulation/run", {
      method: "POST",
      body: JSON.stringify({
        seed: 42,
        merchant_count: 20,
        customers_per_merchant: 100,
        orders_per_customer: 5,
        ...payload,
      }),
    }),

  getAnalyticsReport: (payload = {}) =>
    request("/analytics/report", {
      method: "POST",
      body: JSON.stringify({
        seed: 42,
        merchant_count: 20,
        customers_per_merchant: 100,
        orders_per_customer: 5,
        ...payload,
      }),
    }),

  getPayments: (params = {}) => {
    const query = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (
        value !== undefined &&
        value !== null &&
        value !== ""
      ) {
        query.set(key, String(value));
      }
    });

    const suffix =
      query.toString()
        ? `?${query.toString()}`
        : "";

    return request(
      `/recovery/payments${suffix}`
    );
  },

  getPayment: (paymentId) =>
    request(
      `/recovery/payments/${encodeURIComponent(
        paymentId
      )}`
    ),

  getRecommendations: () =>
    request(
      "/recovery/recommendations"
    ),

  getRecovery: (paymentId) =>
    request(
      `/recovery/${encodeURIComponent(
        paymentId
      )}`
    ),

  getAdaptiveDecision: (paymentId) =>
    request(
      `/recovery/${encodeURIComponent(
        paymentId
      )}/decision`
    ),

  getCounterfactual: (paymentId) =>
    request(
      `/recovery/${encodeURIComponent(
        paymentId
      )}/counterfactual`
    ),

  approveRecovery: (paymentId) =>
    request(
      `/recovery/${encodeURIComponent(
        paymentId
      )}/approve`,
      {
        method: "POST",
      }
    ),

  executeRecovery: (paymentId) =>
    request(
      `/recovery/${encodeURIComponent(
        paymentId
      )}/execute`,
      {
        method: "POST",
      }
    ),
};