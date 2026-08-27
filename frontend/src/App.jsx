import { useEffect, useState } from "react";
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

function App() {
  const [report, setReport] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState("");
  const [error, setError] = useState("");
  const [actionMessage, setActionMessage] = useState("");

  async function loadDashboard() {
    try {
      setLoading(true);
      setError("");
      setActionMessage("");

      // =============================
      // Analytics report
      // =============================

      const reportResponse = await fetch(`${API}/analytics/report`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!reportResponse.ok) {
        throw new Error(
          `Analytics API failed with status ${reportResponse.status}`
        );
      }

      const reportData = await reportResponse.json();
      setReport(reportData);

      // =============================
      // Baseline vs incident
      // =============================

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

      if (comparisonResponse.ok) {
        const comparisonData = await comparisonResponse.json();
        setComparison(comparisonData);
      } else {
        setComparison(null);
      }

      // =============================
      // Recovery recommendations
      // =============================

      const recoveryResponse = await fetch(
        `${API}/recovery/recommendations`
      );

      if (recoveryResponse.ok) {
        const recoveryData = await recoveryResponse.json();
        setRecommendations(recoveryData);
      } else {
        setRecommendations([]);
      }
    } catch (err) {
      console.error("Dashboard loading error:", err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load RecoverX dashboard"
      );
    } finally {
      setLoading(false);
    }
  }

  // =============================
  // Approve recovery
  // =============================

  async function approveRecovery(paymentId) {
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

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to approve recovery"
        );
      }

      setActionMessage(
        `Recovery approved for payment ${paymentId}`
      );

      await loadDashboard();
    } catch (err) {
      console.error("Approval error:", err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to approve recovery"
      );
    } finally {
      setActionLoading("");
    }
  }

  // =============================
  // Execute recovery
  // =============================

  async function executeRecovery(paymentId) {
    try {
      setActionLoading(paymentId);
      setActionMessage("");
      setError("");

      const response = await fetch(
        `${API}/recovery/${paymentId}/execute`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to execute recovery"
        );
      }

      const status = formatLabel(data.status);

      setActionMessage(
        `Recovery executed: ${status} for payment ${paymentId}`
      );

      await loadDashboard();
    } catch (err) {
      console.error("Execution error:", err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to execute recovery"
      );
    } finally {
      setActionLoading("");
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  // =============================
  // Loading
  // =============================

  if (loading) {
    return (
      <div className="app loading-screen">
        <div>
          <div className="logo">RecoverX</div>
          <p>Loading payment intelligence...</p>
        </div>
      </div>
    );
  }

  // =============================
  // Error
  // =============================

  if (error || !report) {
    return (
      <div className="app loading-screen">
        <div className="error-card">
          <h2>Backend connection failed</h2>

          <p>
            {error || "Analytics report could not be loaded."}
          </p>

          <button onClick={loadDashboard}>
            Retry
          </button>

          <small>
            Make sure FastAPI is running on port 8000.
          </small>
        </div>
      </div>
    );
  }

  // =============================
  // Core data
  // =============================

  const metrics = report.metrics || {};
  const incident = report.incident || {};

  // =============================
  // Payment methods
  // =============================

  const methodData = Object.entries(
    report.success_rate_by_method || {}
  ).map(([method, rate]) => ({
    method: method.toUpperCase(),
    success: Number((rate * 100).toFixed(2)),
  }));

  // =============================
  // Failure codes
  // =============================

  const failureCodeData = Object.entries(
    report.failure_code_distribution || {}
  )
    .map(([code, count]) => ({
      code: formatLabel(code),
      count,
    }))
    .sort((a, b) => b.count - a.count);

  // =============================
  // Customer segments
  // =============================

  const segmentData = Object.entries(
    report.failure_rate_by_customer_segment || {}
  )
    .map(([segment, rate]) => ({
      segment: formatLabel(segment),
      failure: Number((rate * 100).toFixed(2)),
    }))
    .sort((a, b) => b.failure - a.failure);

  // =============================
  // Merchant risk
  // =============================

  const merchantData = Object.entries(
    report.failure_rate_by_merchant || {}
  )
    .map(([merchant, rate]) => ({
      merchant,
      failure: Number((rate * 100).toFixed(2)),
    }))
    .sort((a, b) => b.failure - a.failure)
    .slice(0, 8);

  // =============================
  // Recovery revenue
  // =============================

  const recoveryRevenue = recommendations.reduce(
    (sum, item) =>
      sum + Number(item.predicted_revenue || 0),
    0
  );

  // =============================
  // Risk summaries
  // =============================

  const highestRiskSegment = segmentData[0];
  const highestFailureCode = failureCodeData[0];

  // =============================
  // Incident status
  // =============================

  const incidentDetected = Boolean(incident.detected);

  const incidentSeverity = incident.severity
    ? incident.severity.toUpperCase()
    : "NORMAL";

  // =============================
  // Render
  // =============================

  return (
    <div className="app">

      {/* ================= HEADER ================= */}

      <header className="topbar">
        <div>
          <div className="brand">
            RecoverX
          </div>

          <div className="subtitle">
            Payment Recovery Intelligence Platform
          </div>
        </div>

        <div className="header-actions">
          <span
            className={`status-dot ${
              incidentDetected ? "danger" : ""
            }`}
          />

          {incidentDetected
            ? "Incident Detected"
            : "System Operational"}

          <button onClick={loadDashboard}>
            Refresh
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
              Monitor payment failures, detect incidents,
              identify risk, and prioritize recovery actions
              from one intelligence layer.
            </p>
          </div>
        </section>

        {/* ================= KPI METRICS ================= */}

        <section className="metrics-grid">

          <MetricCard
            label="Success Rate"
            value={`${(
              Number(metrics.success_rate || 0) * 100
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
              Number(metrics.failure_rate || 0) * 100
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

        {/* ================= ACTION MESSAGE ================= */}

        {actionMessage && (
          <div className="success-message">
            {actionMessage}
          </div>
        )}

        {/* ================= PERFORMANCE + INCIDENT ================= */}

        <section className="content-grid">

          {/* Payment performance */}

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
                <BarChart data={methodData}>

                  <CartesianGrid
                    strokeDasharray="3 3"
                  />

                  <XAxis dataKey="method" />

                  <YAxis domain={[0, 100]} />

                  <Tooltip
                    formatter={(value) => [
                      `${value}%`,
                      "Success Rate",
                    ]}
                  />

                  <Bar
                    dataKey="success"
                    name="Success %"
                    radius={[6, 6, 0, 0]}
                  />

                </BarChart>
              </ResponsiveContainer>
            </div>

          </div>

          {/* Incident status */}

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
                incidentDetected ? "active" : ""
              }`}
            >

              <div className="incident-icon">
                {incidentDetected ? "!" : "✓"}
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
                    Number(metrics.failure_rate || 0) *
                    100
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
                    comparison.baseline?.failure_rate || 0
                  ) * 100
                ).toFixed(2)}%`}
                incident={`${(
                  Number(
                    comparison.incident?.failure_rate || 0
                  ) * 100
                ).toFixed(2)}%`}
                delta={`+${(
                  Number(
                    comparison.impact?.failure_rate_delta ||
                      0
                  ) * 100
                ).toFixed(2)}%`}
              />

              <ComparisonCard
                label="Failed Payments"
                baseline={Number(
                  comparison.baseline?.failed_payments || 0
                ).toLocaleString()}
                incident={Number(
                  comparison.incident?.failed_payments || 0
                ).toLocaleString()}
                delta={`+${Number(
                  comparison.impact?.failed_payments_delta ||
                    0
                ).toLocaleString()}`}
              />

              <ComparisonCard
                label="Failed Volume"
                baseline={`₹${Number(
                  comparison.baseline?.failed_volume || 0
                ).toLocaleString()}`}
                incident={`₹${Number(
                  comparison.incident?.failed_volume || 0
                ).toLocaleString()}`}
                delta={`+₹${Number(
                  comparison.impact?.failed_volume_delta ||
                    0
                ).toLocaleString()}`}
              />

            </div>

          </section>
        )}

        {/* ================= FAILURE ANALYSIS ================= */}

        <section className="analysis-grid">

          {/* Failure codes */}

          <div className="panel">

            <div className="panel-header">
              <div>
                <h2>
                  Failure Code Distribution
                </h2>

                <span>
                  Root causes behind failed payments
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

                  <XAxis type="number" />

                  <YAxis
                    type="category"
                    dataKey="code"
                    width={135}
                  />

                  <Tooltip />

                  <Bar
                    dataKey="count"
                    name="Failed Payments"
                    radius={[0, 6, 6, 0]}
                  />

                </BarChart>
              </ResponsiveContainer>

            </div>

          </div>

          {/* Customer segments */}

          <div className="panel">

            <div className="panel-header">
              <div>
                <h2>
                  Customer Segment Risk
                </h2>

                <span>
                  Failure rate across customer segments
                </span>
              </div>
            </div>

            <div className="chart">

              <ResponsiveContainer
                width="100%"
                height={320}
              >
                <BarChart data={segmentData}>

                  <CartesianGrid
                    strokeDasharray="3 3"
                  />

                  <XAxis dataKey="segment" />

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
                    radius={[6, 6, 0, 0]}
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
                Merchants ranked by payment failure rate
              </span>
            </div>

            <span className="count-badge">
              Top {merchantData.length}
            </span>

          </div>

          <div className="merchant-table">

            <div className="merchant-row merchant-header">
              <span>Rank</span>
              <span>Merchant ID</span>
              <span>Failure Rate</span>
              <span>Risk</span>
            </div>

            {merchantData.map((merchant, index) => {

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
                    {risk === "high"
                      ? "High"
                      : risk === "medium"
                      ? "Medium"
                      : "Low"}
                  </span>

                </div>
              );
            })}

          </div>

        </section>

        {/* ================= RISK SUMMARY ================= */}

        <section className="risk-summary">

          <div className="risk-summary-card">

            <span className="eyebrow">
              PRIMARY FAILURE DRIVER
            </span>

            <strong>
              {highestFailureCode?.code || "N/A"}
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
              {highestRiskSegment?.segment || "N/A"}
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
              ₹{Number(
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
                Recommended actions for failed payments
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
                  RecoverX did not identify any failed
                  payments requiring recovery.
                </span>
              </div>

            ) : (

              recommendations
                .slice(0, 8)
                .map((recommendation) => {

                  const paymentId =
                    recommendation.payment_id;

                  const isLoading =
                    actionLoading === paymentId;

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
                          {recommendation.reason}
                        </span>

                        <small className="payment-id">
                          Payment: {paymentId}
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

                          <button
                            className="approve-button"
                            disabled={isLoading}
                            onClick={() =>
                              approveRecovery(paymentId)
                            }
                          >
                            {isLoading
                              ? "Processing..."
                              : "Approve"}
                          </button>

                          <button
                            className="execute-button"
                            disabled={isLoading}
                            onClick={() =>
                              executeRecovery(paymentId)
                            }
                          >
                            Execute
                          </button>

                        </div>

                      </div>

                    </div>
                  );
                })

            )}

          </div>

        </section>

      </main>
    </div>
  );
}

// =============================================
// Utility
// =============================================

function formatLabel(value) {
  if (!value) {
    return "N/A";
  }

  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase()
    );
}

// =============================================
// Metric Card
// =============================================

function MetricCard({
  label,
  value,
  detail,
  danger = false,
}) {
  return (
    <div
      className={`metric-card ${
        danger ? "danger-card" : ""
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

// =============================================
// Comparison Card
// =============================================

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