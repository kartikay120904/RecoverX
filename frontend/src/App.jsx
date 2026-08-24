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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDashboard() {
    try {
      setLoading(true);
      setError("");

      const reportResponse = await fetch(`${API}/analytics/report`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!reportResponse.ok) {
        throw new Error("Failed to load analytics report");
      }

      const reportData = await reportResponse.json();
      setReport(reportData);

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
        setComparison(await comparisonResponse.json());
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

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

  if (error) {
    return (
      <div className="app loading-screen">
        <div className="error-card">
          <h2>Backend connection failed</h2>
          <p>{error}</p>

          <button onClick={loadDashboard}>Retry</button>

          <small>
            Make sure FastAPI is running on port 8000.
          </small>
        </div>
      </div>
    );
  }

  const metrics = report.metrics;
  const incident = report.incident;

  const methodData = Object.entries(
    report.success_rate_by_method
  ).map(([method, rate]) => ({
    method: method.toUpperCase(),
    success: Number((rate * 100).toFixed(2)),
  }));

  const recoveryRevenue = report.recovery_recommendations.reduce(
    (sum, item) => sum + Number(item.predicted_revenue || 0),
    0
  );

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <div className="brand">RecoverX</div>

          <div className="subtitle">
            Payment Recovery Intelligence Platform
          </div>
        </div>

        <div className="header-actions">
          <span
            className={`status-dot ${
              incident.detected ? "danger" : ""
            }`}
          />

          {incident.detected
            ? "Incident Detected"
            : "System Operational"}

          <button onClick={loadDashboard}>Refresh</button>
        </div>
      </header>

      <main className="dashboard">
        <section className="hero">
          <div>
            <span className="eyebrow">
              EXECUTIVE OVERVIEW
            </span>

            <h1>Payment health at a glance.</h1>

            <p>
              Monitor failures, detect incidents, and prioritize
              recovery actions from one place.
            </p>
          </div>
        </section>

        <section className="metrics-grid">
          <MetricCard
            label="Success Rate"
            value={`${(metrics.success_rate * 100).toFixed(2)}%`}
            detail={`${metrics.successful_payments.toLocaleString()} successful payments`}
          />

          <MetricCard
            label="Failed Payments"
            value={metrics.failed_payments.toLocaleString()}
            detail={`${(metrics.failure_rate * 100).toFixed(
              2
            )}% failure rate`}
            danger
          />

          <MetricCard
            label="Failed Volume"
            value={`₹${Number(
              metrics.failed_volume
            ).toLocaleString()}`}
            detail={`of ₹${Number(
              metrics.total_volume
            ).toLocaleString()} total volume`}
            danger
          />

          <MetricCard
            label="Recovery Opportunity"
            value={`₹${recoveryRevenue.toLocaleString(undefined, {
              maximumFractionDigits: 0,
            })}`}
            detail={`${report.recovery_recommendations.length} recommendations`}
          />
        </section>

        <section className="content-grid">
          <div className="panel chart-panel">
            <div className="panel-header">
              <div>
                <h2>Payment Performance</h2>

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
                  <CartesianGrid strokeDasharray="3 3" />

                  <XAxis dataKey="method" />

                  <YAxis domain={[0, 100]} />

                  <Tooltip />

                  <Bar
                    dataKey="success"
                    name="Success %"
                    radius={[6, 6, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="panel incident-panel">
            <div className="panel-header">
              <div>
                <h2>Incident Status</h2>

                <span>
                  Current system assessment
                </span>
              </div>
            </div>

            <div
              className={`incident-state ${
                incident.detected ? "active" : ""
              }`}
            >
              <div className="incident-icon">
                {incident.detected ? "!" : "✓"}
              </div>

              <div>
                <strong>
                  {incident.detected
                    ? `${incident.severity.toUpperCase()} INCIDENT`
                    : "SYSTEM NORMAL"}
                </strong>

                <p>
                  {incident.detected
                    ? `${incident.affected_payments.toLocaleString()} payments affected`
                    : "No significant payment incident detected"}
                </p>
              </div>
            </div>

            <div className="incident-stats">
              <div>
                <span>Failure Rate</span>

                <strong>
                  {(metrics.failure_rate * 100).toFixed(2)}%
                </strong>
              </div>

              <div>
                <span>Strategy</span>

                <strong>
                  {incident.recommended_strategy.replaceAll(
                    "_",
                    " "
                  )}
                </strong>
              </div>
            </div>
          </div>
        </section>

        {comparison && (
          <section className="panel comparison-panel">
            <div className="panel-header">
              <div>
                <h2>Baseline vs Incident</h2>

                <span>
                  Impact of simulated payment infrastructure
                  incidents
                </span>
              </div>
            </div>

            <div className="comparison-grid">
              <ComparisonCard
                label="Failure Rate"
                baseline={`${(
                  comparison.baseline.failure_rate * 100
                ).toFixed(2)}%`}
                incident={`${(
                  comparison.incident.failure_rate * 100
                ).toFixed(2)}%`}
                delta={`+${(
                  comparison.impact.failure_rate_delta * 100
                ).toFixed(2)}%`}
              />

              <ComparisonCard
                label="Failed Payments"
                baseline={comparison.baseline.failed_payments.toLocaleString()}
                incident={comparison.incident.failed_payments.toLocaleString()}
                delta={`+${comparison.impact.failed_payments_delta.toLocaleString()}`}
              />

              <ComparisonCard
                label="Failed Volume"
                baseline={`₹${Number(
                  comparison.baseline.failed_volume
                ).toLocaleString()}`}
                incident={`₹${Number(
                  comparison.incident.failed_volume
                ).toLocaleString()}`}
                delta={`+₹${Number(
                  comparison.impact.failed_volume_delta
                ).toLocaleString()}`}
              />
            </div>
          </section>
        )}

        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>Recovery Recommendations</h2>

              <span>
                Recommended actions for failed payments
              </span>
            </div>

            <span className="count-badge">
              {report.recovery_recommendations.length}
            </span>
          </div>

          <div className="recommendations">
            {report.recovery_recommendations
              .slice(0, 8)
              .map((recommendation) => (
                <div
                  className="recommendation"
                  key={recommendation.payment_id}
                >
                  <div className="recommendation-main">
                    <strong>
                      {recommendation.strategy.replaceAll(
                        "_",
                        " "
                      )}
                    </strong>

                    <span>
                      {recommendation.reason}
                    </span>
                  </div>

                  <div className="recommendation-value">
                    <strong>
                      {(
                        recommendation.predicted_probability *
                        100
                      ).toFixed(0)}
                      %
                    </strong>

                    <span>
                      ₹
                      {Number(
                        recommendation.predicted_revenue
                      ).toLocaleString()}
                    </span>
                  </div>
                </div>
              ))}
          </div>
        </section>
      </main>
    </div>
  );
}

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
      <span>{label}</span>

      <strong>{value}</strong>

      <small>{detail}</small>
    </div>
  );
}

function ComparisonCard({
  label,
  baseline,
  incident,
  delta,
}) {
  return (
    <div className="comparison-card">
      <span>{label}</span>

      <div>
        <small>Baseline</small>
        <strong>{baseline}</strong>
      </div>

      <div>
        <small>Incident</small>
        <strong>{incident}</strong>
      </div>

      <div className="delta">
        <small>Impact</small>
        <strong>{delta}</strong>
      </div>
    </div>
  );
}

export default App;
