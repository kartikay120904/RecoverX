import { useEffect, useState } from "react";
import { api } from "./services/api";
import PaymentOperations from "./components/PaymentOperations";
import RecoveryPanel from "./components/RecoveryPanel";
import DecisionAnalysis from "./components/DecisionAnalysis";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import "./App.css";

const API = "http://127.0.0.1:8000";

// =============================================================
// Razorpay Checkout Script Loader
// =============================================================

function loadRazorpayScript() {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }

    const existingScript = document.querySelector(
      'script[src="https://checkout.razorpay.com/v1/checkout.js"]'
    );

    if (existingScript) {
      existingScript.addEventListener("load", () => resolve(true));
      existingScript.addEventListener("error", () => resolve(false));
      return;
    }

    const script = document.createElement("script");

    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;

    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);

    document.body.appendChild(script);
  });
}

// =============================================================
// Utility Functions
// =============================================================

function formatLabel(value) {
  if (!value) {
    return "N/A";
  }

  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

async function getResponseData(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

function getErrorMessage(data, fallback) {
  if (!data) {
    return fallback;
  }

  if (typeof data.detail === "string") {
    return data.detail;
  }

  if (typeof data.message === "string") {
    return data.message;
  }

  if (typeof data.error === "string") {
    return data.error;
  }

  return fallback;
}

// =============================================================
// Application
// =============================================================

function App() {
  const [report, setReport] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [recoveryStatuses, setRecoveryStatuses] = useState({});

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const [actionLoading, setActionLoading] = useState("");
  const [paymentLoading, setPaymentLoading] = useState("");

  const [error, setError] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  
  const [backendStatus, setBackendStatus] = useState("Checking backend...");
  useEffect(() => {
  api.health()
    .then(() => {
      setBackendStatus("Backend connected");
    })
    .catch((error) => {
      console.error("Backend connection failed:", error);
      setBackendStatus("Backend unavailable");
    });
}, []);

  <div className="backend-status">
  {backendStatus}
</div>

  // =========================================================
  // Load Dashboard
  // =========================================================

  async function loadDashboard() {
    try {
      setLoading(true);
      setError("");
      setActionMessage("");

      // =====================================================
      // Analytics Report
      // =====================================================

      const reportResponse = await fetch(
        `${API}/analytics/report`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            seed: 42,
            merchant_count: 20,
            customers_per_merchant: 100,
            orders_per_customer: 5,
          }),
        }
      );

      const reportData = await getResponseData(
        reportResponse
      );

      if (!reportResponse.ok) {
        throw new Error(
          getErrorMessage(
            reportData,
            `Analytics API failed with status ${reportResponse.status}`
          )
        );
      }

      setReport(reportData);

      // =====================================================
      // Baseline vs Incident Comparison
      // =====================================================

      const comparisonResponse = await fetch(
        `${API}/simulation/compare`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            baseline_config: {
              seed: 42,
              merchant_count: 20,
              customers_per_merchant: 100,
              orders_per_customer: 5,
              enable_upi_degradation: false,
              enable_gateway_outage: false,
            },

            incident_config: {
              seed: 42,
              merchant_count: 20,
              customers_per_merchant: 100,
              orders_per_customer: 5,
              enable_upi_degradation: true,
              enable_gateway_outage: true,
            },
          }),
        }
      );

      const comparisonData = await getResponseData(
        comparisonResponse
      );

      if (comparisonResponse.ok) {
        setComparison(comparisonData);
      } else {
        setComparison(null);
      }

      // =====================================================
      // Recovery Recommendations
      // =====================================================

      const recoveryResponse = await fetch(
        `${API}/recovery/recommendations`
      );

      const recoveryData = await getResponseData(
        recoveryResponse
      );

      if (recoveryResponse.ok) {
        const safeRecoveryData = Array.isArray(
          recoveryData
        )
          ? recoveryData
          : [];

        setRecommendations(safeRecoveryData);

        const statuses = {};

        safeRecoveryData.forEach((item) => {
          if (item?.payment_id && item?.status) {
            statuses[item.payment_id] =
              item.status;
          }
        });

        setRecoveryStatuses((previous) => ({
          ...previous,
          ...statuses,
        }));
      } else {
        setRecommendations([]);
      }
    } catch (err) {
      console.error(
        "Dashboard loading error:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load RecoverX dashboard"
      );
    } finally {
      setLoading(false);
    }
  }

  // =========================================================
  // Refresh Dashboard
  // =========================================================

  async function refreshDashboard() {
    if (refreshing) {
      return;
    }

    try {
      setRefreshing(true);
      await loadDashboard();
    } finally {
      setRefreshing(false);
    }
  }

  // =========================================================
  // Approve Recovery
  // =========================================================

  async function approveRecovery(paymentId) {
    if (!paymentId) {
      setError(
        "Payment ID is required to approve recovery."
      );
      return;
    }

    if (actionLoading || paymentLoading) {
      return;
    }

    try {
      setActionLoading(paymentId);
      setActionMessage("");
      setError("");

      const response = await fetch(
        `${API}/recovery/${paymentId}/approve`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      const data = await getResponseData(response);

      if (!response.ok) {
        throw new Error(
          getErrorMessage(
            data,
            "Failed to approve recovery."
          )
        );
      }

      setRecoveryStatuses((previous) => ({
        ...previous,
        [paymentId]:
          data.status || "approved",
      }));

      setActionMessage(
        `Recovery approved for payment ${paymentId}`
      );
    } catch (err) {
      console.error(
        "Approval error:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to approve recovery."
      );
    } finally {
      setActionLoading("");
    }
  }

  // =========================================================
  // Execute Recovery
  // =========================================================

  async function executeRecovery(paymentId) {
    if (!paymentId) {
      setError(
        "Payment ID is required to execute recovery."
      );
      return;
    }

    if (actionLoading || paymentLoading) {
      return;
    }

    try {
      setActionLoading(paymentId);
      setActionMessage("");
      setError("");

      const currentStatus =
        recoveryStatuses[paymentId];

      if (currentStatus !== "approved") {
        throw new Error(
          "Recovery must be approved before execution."
        );
      }

      const response = await fetch(
        `${API}/recovery/${paymentId}/execute`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      const data = await getResponseData(response);

      if (!response.ok) {
        throw new Error(
          getErrorMessage(
            data,
            "Failed to execute recovery."
          )
        );
      }

      const newStatus =
        data.status || "succeeded";

      setRecoveryStatuses((previous) => ({
        ...previous,
        [paymentId]: newStatus,
      }));

      setActionMessage(
        `Recovery executed: ${formatLabel(
          newStatus
        )} for payment ${paymentId}`
      );
    } catch (err) {
      console.error(
        "Execution error:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to execute recovery."
      );
    } finally {
      setActionLoading("");
    }
  }

  // =========================================================
  // Razorpay Test Mode Checkout
  // =========================================================

  async function openRazorpayCheckout(
    recommendation
  ) {
    const paymentId =
      recommendation?.payment_id;

    if (!paymentId) {
      setError(
        "Payment ID is missing for this recovery."
      );
      return;
    }

    if (actionLoading || paymentLoading) {
      return;
    }

    try {
      setPaymentLoading(paymentId);
      setError("");
      setActionMessage("");

      // =====================================================
      // Load Razorpay Checkout
      // =====================================================

      const scriptLoaded =
        await loadRazorpayScript();

      if (
        !scriptLoaded ||
        !window.Razorpay
      ) {
        throw new Error(
          "Razorpay Checkout could not be loaded. Please check your internet connection."
        );
      }

      // =====================================================
      // Determine Recovery Amount
      // =====================================================

      const predictedRevenue = Number(
        recommendation.predicted_revenue || 0
      );

      if (
        !Number.isFinite(
          predictedRevenue
        ) ||
        predictedRevenue <= 0
      ) {
        throw new Error(
          "A valid recovery amount is required before starting payment."
        );
      }

      // Razorpay expects INR amount in paise.

      const amount = Math.round(
        predictedRevenue * 100
      );

      if (amount <= 0) {
        throw new Error(
          "The Razorpay order amount must be greater than zero."
        );
      }

      // =====================================================
      // Create Razorpay Test Mode Order
      // =====================================================

      const orderResponse = await fetch(
        `${API}/razorpay/order`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            amount,
            currency: "INR",
            receipt: `recoverx_${paymentId}`,
          }),
        }
      );

      const orderData =
        await getResponseData(
          orderResponse
        );

      if (!orderResponse.ok) {
        throw new Error(
          getErrorMessage(
            orderData,
            "Unable to create Razorpay order."
          )
        );
      }

      if (orderData.mode !== "test") {
        throw new Error(
          "RecoverX Razorpay integration is not running in Test Mode."
        );
      }

      const order = orderData.order;

      if (!order?.id) {
        throw new Error(
          "Razorpay returned an invalid order."
        );
      }

      // =====================================================
      // Get Razorpay Public Test Key
      // =====================================================

      const configResponse = await fetch(
        `${API}/razorpay/config`
      );

      const configData =
        await getResponseData(
          configResponse
        );

      if (
        !configResponse.ok ||
        !configData.key_id
      ) {
        throw new Error(
          "Razorpay configuration could not be loaded."
        );
      }

      if (
        configData.mode !== "test"
      ) {
        throw new Error(
          "RecoverX payment checkout is not running in Test Mode."
        );
      }

      // =====================================================
      // Razorpay Checkout Options
      // =====================================================

      const options = {
        key: configData.key_id,

        amount: order.amount,

        currency:
          order.currency || "INR",

        name: "RecoverX",

        description:
          "Payment Recovery",

        order_id: order.id,

        handler: async function (
          response
        ) {
          try {
            setPaymentLoading(
              paymentId
            );

            setError("");
            setActionMessage("");

            // ===============================================
            // Server-side Signature Verification
            // ===============================================

            const verifyResponse =
              await fetch(
                `${API}/razorpay/verify`,
                {
                  method: "POST",

                  headers: {
                    "Content-Type":
                      "application/json",
                  },

                  body: JSON.stringify({
                    razorpay_order_id:
                      response.razorpay_order_id,

                    razorpay_payment_id:
                      response.razorpay_payment_id,

                    razorpay_signature:
                      response.razorpay_signature,
                  }),
                }
              );

            const verifyData =
              await getResponseData(
                verifyResponse
              );

            if (
              !verifyResponse.ok
            ) {
              throw new Error(
                getErrorMessage(
                  verifyData,
                  "Payment verification failed."
                )
              );
            }

            if (
              !verifyData.verified
            ) {
              throw new Error(
                "Razorpay payment could not be verified."
              );
            }

            setActionMessage(
              `Payment verified successfully for recovery ${paymentId}`
            );
          } catch (err) {
            console.error(
              "Razorpay verification error:",
              err
            );

            setError(
              err instanceof Error
                ? err.message
                : "Payment verification failed."
            );
          } finally {
            setPaymentLoading("");
          }
        },

        modal: {
          ondismiss: function () {
            setPaymentLoading("");

            setActionMessage(
              "Razorpay checkout was closed."
            );
          },
        },

        theme: {
          color: "#111827",
        },
      };

      // =====================================================
      // Open Razorpay Checkout
      // =====================================================

      const razorpay =
        new window.Razorpay(
          options
        );

      razorpay.on(
        "payment.failed",
        function (response) {
          console.error(
            "Razorpay payment failed:",
            response
          );

          const description =
            response?.error
              ?.description ||
            "Razorpay payment failed.";

          setError(description);

          setPaymentLoading("");
        }
      );

      razorpay.open();
    } catch (err) {
      console.error(
        "Razorpay checkout error:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to start Razorpay checkout."
      );

      setPaymentLoading("");
    }
  }
  <PaymentOperations />


  // =========================================================
  // Initial Load
  // =========================================================

  useEffect(() => {
    loadDashboard();
  }, []);

  // =========================================================
  // Loading Screen
  // =========================================================

  if (loading) {
    return (
      <div className="app loading-screen">
        <div>
          <div className="logo">
            RecoverX
          </div>

          <p>
            Loading payment intelligence...
          </p>
        </div>
      </div>
    );
  }

  // =========================================================
  // Backend Connection Error
  // =========================================================

  if (!report) {
    return (
      <div className="app loading-screen">
        <div className="error-card">
          <h2>
            Backend connection failed
          </h2>

          <p>
            {error ||
              "Analytics report could not be loaded."}
          </p>

          <button
            onClick={loadDashboard}
          >
            Retry
          </button>

          <small>
            Make sure FastAPI is running on
            port 8000.
          </small>
        </div>
      </div>
    );
  }
  <RecoveryPanel />
  // =========================================================
  // Core Data
  // =========================================================

  const metrics =
    report.metrics || {};

  const incident =
    report.incident || {};

  // =========================================================
  // Payment Methods
  // =========================================================

  const methodData =
    Object.entries(
      report.success_rate_by_method || {}
    ).map(
      ([method, rate]) => ({
        method:
          method.toUpperCase(),

        success: Number(
          (
            Number(rate) * 100
          ).toFixed(2)
        ),
      })
    );

  // =========================================================
  // Failure Codes
  // =========================================================

  const failureCodeData =
    Object.entries(
      report.failure_code_distribution || {}
    )
      .map(
        ([code, count]) => ({
          code:
            formatLabel(code),

          count:
            Number(count) || 0,
        })
      )
      .sort(
        (a, b) =>
          b.count - a.count
      );

  // =========================================================
  // Customer Segments
  // =========================================================

  const segmentData =
    Object.entries(
      report.failure_rate_by_customer_segment ||
        {}
    )
      .map(
        ([segment, rate]) => ({
          segment:
            formatLabel(segment),

          failure: Number(
            (
              Number(rate) * 100
            ).toFixed(2)
          ),
        })
      )
      .sort(
        (a, b) =>
          b.failure - a.failure
      );

  // =========================================================
  // Merchant Risk
  // =========================================================

  const merchantData =
    Object.entries(
      report.failure_rate_by_merchant || {}
    )
      .map(
        ([merchant, rate]) => ({
          merchant,

          failure: Number(
            (
              Number(rate) * 100
            ).toFixed(2)
          ),
        })
      )
      .sort(
        (a, b) =>
          b.failure - a.failure
      )
      .slice(0, 8);

  // =========================================================
  // Recovery Revenue
  // =========================================================

  const recoveryRevenue =
    recommendations.reduce(
      (sum, item) =>
        sum +
        Number(
          item?.predicted_revenue || 0
        ),
      0
    );

  <DecisionAnalysis />

  // =========================================================
  // Risk Summary
  // =========================================================

  const highestRiskSegment =
    segmentData[0];

  const highestFailureCode =
    failureCodeData[0];

  // =========================================================
  // Incident Status
  // =========================================================

  const incidentDetected =
    Boolean(incident.detected);

  const incidentSeverity =
    incident.severity
      ? String(
          incident.severity
        ).toUpperCase()
      : "NORMAL";

  // =========================================================
  // Dashboard
  // =========================================================

  return (
    <div className="app">

      {/* ================= HEADER ================= */}

      <header className="topbar">
        <div>
          <div className="brand">
            RecoverX
          </div>

          <div className="subtitle">
            Payment Recovery Intelligence
            Platform
          </div>
        </div>

        <div className="header-actions">
          <span
            className={`status-dot ${
              incidentDetected
                ? "danger"
                : ""
            }`}
          />

          <span>
            {incidentDetected
              ? "Incident Detected"
              : "System Operational"}
          </span>

          <button
            onClick={refreshDashboard}
            disabled={refreshing}
          >
            {refreshing
              ? "Refreshing..."
              : "Refresh"}
          </button>
        </div>
      </header>

      <main className="dashboard">

        {/* ================= HERO ================= */}

        <section className="hero">
          <div>
            <span className="eyebrow">
              EXECUTIVE OVERVIEW
            </span>

            <h1>
              Payment health at a glance.
            </h1>

            <p>
              Monitor payment failures,
              detect incidents, identify
              risk, and prioritize recovery
              actions from one intelligence
              layer.
            </p>
          </div>
        </section>

        {/* ================= KPI METRICS ================= */}

        <section className="metrics-grid">

          <MetricCard
            label="Success Rate"
            value={`${(
              Number(
                metrics.success_rate || 0
              ) * 100
            ).toFixed(2)}%`}
            detail={`${Number(
              metrics.successful_payments || 0
            ).toLocaleString()} successful payments`}
          />

          <MetricCard
            label="Failed Payments"
            value={Number(
              metrics.failed_payments || 0
            ).toLocaleString()}
            detail={`${(
              Number(
                metrics.failure_rate || 0
              ) * 100
            ).toFixed(2)}% failure rate`}
            danger
          />

          <MetricCard
            label="Failed Volume"
            value={`₹${Number(
              metrics.failed_volume || 0
            ).toLocaleString()}`}
            detail={`of ₹${Number(
              metrics.total_volume || 0
            ).toLocaleString()} total volume`}
            danger
          />

          <MetricCard
            label="Recovery Opportunity"
            value={`₹${recoveryRevenue.toLocaleString(
              undefined,
              {
                maximumFractionDigits: 0,
              }
            )}`}
            detail={`${recommendations.length} recommendations`}
          />

        </section>

        {/* ================= MESSAGES ================= */}

        {actionMessage && (
          <div className="success-message">
            {actionMessage}
          </div>
        )}

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {/* ================= PERFORMANCE ================= */}

        <section className="content-grid">

          <div className="panel chart-panel">

            <div className="panel-header">
              <div>
                <h2>
                  Payment Performance
                </h2>

                <span>
                  Success rate by payment method
                </span>
              </div>
            </div>

            <div className="chart">

              <ResponsiveContainer
                width="100%"
                height={300}
              >
                <BarChart
                  data={methodData}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="method"
                  />

                  <YAxis
                    domain={[0, 100]}
                  />

                  <Tooltip
                    formatter={(value) => [
                      `${value}%`,
                      "Success Rate",
                    ]}
                  />

                  <Bar
                    dataKey="success"
                    name="Success %"
                    radius={[
                      6,
                      6,
                      0,
                      0,
                    ]}
                  />

                </BarChart>
              </ResponsiveContainer>

            </div>
          </div>

          {/* ================= INCIDENT ================= */}

          <div className="panel incident-panel">

            <div className="panel-header">
              <div>
                <h2>
                  Incident Status
                </h2>

                <span>
                  Current system assessment
                </span>
              </div>
            </div>

            <div
              className={`incident-state ${
                incidentDetected
                  ? "active"
                  : ""
              }`}
            >

              <div className="incident-icon">
                {incidentDetected
                  ? "!"
                  : "✓"}
              </div>

              <div>

                <strong>
                  {incidentDetected
                    ? `${incidentSeverity} INCIDENT`
                    : "SYSTEM NORMAL"}
                </strong>

                <p>
                  {incidentDetected
                    ? `${Number(
                        incident.affected_payments || 0
                      ).toLocaleString()} payments affected`
                    : "No significant payment incident detected"}
                </p>

              </div>

            </div>

            <div className="incident-stats">

              <div>
                <span>
                  Failure Rate
                </span>

                <strong>
                  {(
                    Number(
                      metrics.failure_rate || 0
                    ) * 100
                  ).toFixed(2)}
                  %
                </strong>
              </div>

              <div>
                <span>
                  Strategy
                </span>

                <strong>
                  {formatLabel(
                    incident.recommended_strategy ||
                      "no_action"
                  )}
                </strong>
              </div>

            </div>

          </div>

        </section>

        {/* ================= BASELINE VS INCIDENT ================= */}

        {comparison && (

          <section className="panel comparison-panel">

            <div className="panel-header">
              <div>
                <h2>
                  Baseline vs Incident
                </h2>

                <span>
                  Impact of simulated payment
                  infrastructure incidents
                </span>
              </div>
            </div>

            <div className="comparison-grid">

              <ComparisonCard
                label="Failure Rate"
                baseline={`${(
                  Number(
                    comparison.baseline
                      ?.failure_rate || 0
                  ) * 100
                ).toFixed(2)}%`}
                incident={`${(
                  Number(
                    comparison.incident
                      ?.failure_rate || 0
                  ) * 100
                ).toFixed(2)}%`}
                delta={`+${(
                  Number(
                    comparison.impact
                      ?.failure_rate_delta || 0
                  ) * 100
                ).toFixed(2)}%`}
              />

              <ComparisonCard
                label="Failed Payments"
                baseline={Number(
                  comparison.baseline
                    ?.failed_payments || 0
                ).toLocaleString()}
                incident={Number(
                  comparison.incident
                    ?.failed_payments || 0
                ).toLocaleString()}
                delta={`+${Number(
                  comparison.impact
                    ?.failed_payments_delta || 0
                ).toLocaleString()}`}
              />

              <ComparisonCard
                label="Failed Volume"
                baseline={`₹${Number(
                  comparison.baseline
                    ?.failed_volume || 0
                ).toLocaleString()}`}
                incident={`₹${Number(
                  comparison.incident
                    ?.failed_volume || 0
                ).toLocaleString()}`}
                delta={`+₹${Number(
                  comparison.impact
                    ?.failed_volume_delta || 0
                ).toLocaleString()}`}
              />

            </div>

          </section>

        )}

        {/* ================= FAILURE ANALYSIS ================= */}

        <section className="analysis-grid">

          <div className="panel">

            <div className="panel-header">
              <div>
                <h2>
                  Failure Code Distribution
                </h2>

                <span>
                  Root causes behind failed
                  payments
                </span>
              </div>
            </div>

            <div className="chart">

              <ResponsiveContainer
                width="100%"
                height={320}
              >

                <BarChart
                  data={failureCodeData}
                  layout="vertical"
                  margin={{
                    left: 20,
                    right: 20,
                  }}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    type="number"
                  />

                  <YAxis
                    type="category"
                    dataKey="code"
                    width={135}
                  />

                  <Tooltip />

                  <Bar
                    dataKey="count"
                    name="Failed Payments"
                    radius={[
                      0,
                      6,
                      6,
                      0,
                    ]}
                  />

                </BarChart>

              </ResponsiveContainer>

            </div>

          </div>

          {/* ================= CUSTOMER SEGMENTS ================= */}

          <div className="panel">

            <div className="panel-header">
              <div>
                <h2>
                  Customer Segment Risk
                </h2>

                <span>
                  Failure rate across customer
                  segments
                </span>
              </div>
            </div>

            <div className="chart">

              <ResponsiveContainer
                width="100%"
                height={320}
              >

                <BarChart
                  data={segmentData}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="segment"
                  />

                  <YAxis
                    domain={[0, "auto"]}
                    tickFormatter={(value) =>
                      `${value}%`
                    }
                  />

                  <Tooltip
                    formatter={(value) => [
                      `${value}%`,
                      "Failure Rate",
                    ]}
                  />

                  <Bar
                    dataKey="failure"
                    name="Failure Rate"
                    radius={[
                      6,
                      6,
                      0,
                      0,
                    ]}
                  />

                </BarChart>

              </ResponsiveContainer>

            </div>

          </div>

        </section>

        {/* ================= MERCHANT RISK ================= */}

        <section className="panel merchant-panel">

          <div className="panel-header">

            <div>
              <h2>
                Highest-Risk Merchants
              </h2>

              <span>
                Merchants ranked by payment
                failure rate
              </span>
            </div>

            <span className="count-badge">
              Top {merchantData.length}
            </span>

          </div>

          <div className="merchant-table">

            <div className="merchant-row merchant-header">

              <span>
                Rank
              </span>

              <span>
                Merchant ID
              </span>

              <span>
                Failure Rate
              </span>

              <span>
                Risk
              </span>

            </div>

            {merchantData.map(
              (merchant, index) => {

                const risk =
                  merchant.failure >= 15
                    ? "high"
                    : merchant.failure >= 13
                    ? "medium"
                    : "low";

                return (
                  <div
                    className="merchant-row"
                    key={merchant.merchant}
                  >

                    <span className="merchant-rank">
                      #{index + 1}
                    </span>

                    <span className="merchant-id">
                      {merchant.merchant}
                    </span>

                    <strong className="merchant-rate">
                      {merchant.failure}%
                    </strong>

                    <span
                      className={`risk-badge ${risk}`}
                    >
                      {formatLabel(risk)}
                    </span>

                  </div>
                );
              }
            )}

          </div>

        </section>

        {/* ================= RISK SUMMARY ================= */}

        <section className="risk-summary">

          <div className="risk-summary-card">

            <span className="eyebrow">
              PRIMARY FAILURE DRIVER
            </span>

            <strong>
              {highestFailureCode?.code ||
                "N/A"}
            </strong>

            <p>
              {highestFailureCode
                ? `${highestFailureCode.count.toLocaleString()} failed payments`
                : "No failure data available"}
            </p>

          </div>

          <div className="risk-summary-card">

            <span className="eyebrow">
              HIGHEST-RISK CUSTOMER SEGMENT
            </span>

            <strong>
              {highestRiskSegment?.segment ||
                "N/A"}
            </strong>

            <p>
              {highestRiskSegment
                ? `${highestRiskSegment.failure}% failure rate`
                : "No segment data available"}
            </p>

          </div>

          <div className="risk-summary-card">

            <span className="eyebrow">
              AFFECTED PAYMENT VOLUME
            </span>

            <strong>
              ₹
              {Number(
                incident.affected_volume || 0
              ).toLocaleString()}
            </strong>

            <p>
              Across{" "}
              {Number(
                incident.affected_payments || 0
              ).toLocaleString()}{" "}
              affected payments
            </p>

          </div>

        </section>

        {/* ================= RECOVERY RECOMMENDATIONS ================= */}

        <section className="panel">

          <div className="panel-header">

            <div>
              <h2>
                Recovery Recommendations
              </h2>

              <span>
                Recommended actions for failed
                payments
              </span>
            </div>

            <span className="count-badge">
              {recommendations.length}
            </span>

          </div>

          <div className="recommendations">

            {recommendations.length === 0 ? (

              <div className="empty-state">

                <strong>
                  No recovery actions required
                </strong>

                <span>
                  RecoverX did not identify any
                  failed payments requiring
                  recovery.
                </span>

              </div>

            ) : (

              recommendations
                .slice(0, 8)
                .map(
                  (recommendation) => {

                    const paymentId =
                      recommendation.payment_id;

                    const isActionLoading =
                      actionLoading ===
                      paymentId;

                    const isPaymentLoading =
                      paymentLoading ===
                      paymentId;

                    const status =
                      recoveryStatuses[
                        paymentId
                      ] ||
                      recommendation.status ||
                      "proposed";

                    return (

                      <div
                        className="recommendation"
                        key={paymentId}
                      >

                        <div className="recommendation-main">

                          <strong>
                            {formatLabel(
                              recommendation.strategy
                            )}
                          </strong>

                          <span>
                            {recommendation.reason ||
                              "Recovery strategy recommended by RecoverX."}
                          </span>

                          <small className="payment-id">
                            Payment:{" "}
                            {paymentId}
                          </small>

                        </div>

                        <div className="recommendation-value">

                          <strong>
                            {(
                              Number(
                                recommendation.predicted_probability ||
                                  0
                              ) * 100
                            ).toFixed(0)}
                            %
                          </strong>

                          <span>
                            ₹
                            {Number(
                              recommendation.predicted_revenue ||
                                0
                            ).toLocaleString()}
                          </span>

                          <div className="recovery-actions">

                            {/* APPROVE */}

                            {status ===
                              "proposed" && (

                              <button
                                className="approve-button"
                                disabled={
                                  isActionLoading ||
                                  isPaymentLoading
                                }
                                onClick={() =>
                                  approveRecovery(
                                    paymentId
                                  )
                                }
                              >
                                {isActionLoading
                                  ? "Approving..."
                                  : "Approve"}
                              </button>

                            )}

                            {/* EXECUTE */}

                            {status ===
                              "approved" && (

                              <button
                                className="execute-button"
                                disabled={
                                  isActionLoading ||
                                  isPaymentLoading
                                }
                                onClick={() =>
                                  executeRecovery(
                                    paymentId
                                  )
                                }
                              >
                                {isActionLoading
                                  ? "Executing..."
                                  : "Execute Recovery"}
                              </button>

                            )}

                            {/* RAZORPAY */}

                            {status ===
                              "approved" && (

                              <button
                                className="razorpay-button"
                                disabled={
                                  isActionLoading ||
                                  isPaymentLoading
                                }
                                onClick={() =>
                                  openRazorpayCheckout(
                                    recommendation
                                  )
                                }
                              >
                                {isPaymentLoading
                                  ? "Opening Checkout..."
                                  : "Pay with Razorpay"}
                              </button>

                            )}

                            {/* SUCCESS */}

                            {status ===
                              "succeeded" && (

                              <span className="status-badge succeeded">
                                ✓ Recovered
                              </span>

                            )}

                            {/* FAILED */}

                            {status ===
                              "failed" && (

                              <span className="status-badge failed">
                                Failed
                              </span>

                            )}

                            {/* OTHER */}

                            {![
                              "proposed",
                              "approved",
                              "succeeded",
                              "failed",
                            ].includes(
                              status
                            ) && (

                              <span className="status-badge">
                                {formatLabel(
                                  status
                                )}
                              </span>

                            )}

                          </div>

                        </div>

                      </div>

                    );
                  }
                )

            )}

          </div>

        </section>

      </main>

    </div>
  );
}

// =============================================================
// Metric Card
// =============================================================

function MetricCard({
  label,
  value,
  detail,
  danger = false,
}) {
  return (
    <div
      className={`metric-card ${
        danger
          ? "danger-card"
          : ""
      }`}
    >

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

      <small>
        {detail}
      </small>

    </div>
  );
}

// =============================================================
// Comparison Card
// =============================================================

function ComparisonCard({
  label,
  baseline,
  incident,
  delta,
}) {
  return (
    <div className="comparison-card">

      <span>
        {label}
      </span>

      <div>
        <small>
          Baseline
        </small>

        <strong>
          {baseline}
        </strong>
      </div>

      <div>
        <small>
          Incident
        </small>

        <strong>
          {incident}
        </strong>
      </div>

      <div className="delta">
        <small>
          Impact
        </small>

        <strong>
          {delta}
        </strong>
      </div>

    </div>
  );
}

export default App;