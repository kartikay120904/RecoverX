import { useState } from "react";
import { api } from "../services/api";

export default function RecoveryPanel() {
  const [paymentId, setPaymentId] = useState("");
  const [recommendation, setRecommendation] = useState(null);

  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const loadRecovery = async () => {
    if (!paymentId.trim()) {
      setError("Enter a valid payment ID.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setSuccessMessage("");
      setRecommendation(null);

      const data = await api.getRecovery(paymentId.trim());

      setRecommendation(data);
    } catch (err) {
      console.error("Failed to load recovery:", err);
      setError(
        err.message || "Unable to load recovery information."
      );
    } finally {
      setLoading(false);
    }
  };

  const approveRecovery = async () => {
    try {
      setActionLoading(true);
      setError("");
      setSuccessMessage("");

      const result = await api.approveRecovery(
        paymentId.trim()
      );

      setRecommendation((previous) => ({
        ...(previous || {}),
        ...result,
      }));

      setSuccessMessage(
        "Recovery approved successfully."
      );
    } catch (err) {
      console.error("Recovery approval failed:", err);

      setError(
        err.message || "Unable to approve recovery."
      );
    } finally {
      setActionLoading(false);
    }
  };

  const executeRecovery = async () => {
    try {
      setActionLoading(true);
      setError("");
      setSuccessMessage("");

      const result = await api.executeRecovery(
        paymentId.trim()
      );

      setRecommendation((previous) => ({
        ...(previous || {}),
        ...result,
      }));

      setSuccessMessage(
        "Recovery executed successfully."
      );
    } catch (err) {
      console.error("Recovery execution failed:", err);

      setError(
        err.message || "Unable to execute recovery."
      );
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <section className="recovery-panel">
      <div className="section-header">
        <div>
          <h2>Recovery Control Center</h2>

          <p>
            Investigate a payment and execute a
            controlled recovery workflow.
          </p>
        </div>
      </div>

      <div className="recovery-search">
        <input
          type="text"
          placeholder="Enter payment ID"
          value={paymentId}
          onChange={(event) =>
            setPaymentId(event.target.value)
          }
        />

        <button
          type="button"
          onClick={loadRecovery}
          disabled={loading}
        >
          {loading
            ? "Investigating..."
            : "Investigate"}
        </button>
      </div>

      {error && (
        <div className="recovery-error">
          {error}
        </div>
      )}

      {successMessage && (
        <div className="recovery-success">
          {successMessage}
        </div>
      )}

      {recommendation && (
        <div className="recovery-result">
          <h3>Recovery Recommendation</h3>

          <div className="recovery-grid">
            <div className="recovery-card">
              <span>Payment ID</span>

              <strong>
                {recommendation.payment_id ||
                  paymentId}
              </strong>
            </div>

            <div className="recovery-card">
              <span>Status</span>

              <strong>
                {recommendation.status ||
                  recommendation.state ||
                  "Available"}
              </strong>
            </div>

            <div className="recovery-card">
              <span>Action</span>

              <strong>
                {recommendation.action ||
                  recommendation.recommended_action ||
                  recommendation.recovery_action ||
                  "Review required"}
              </strong>
            </div>

            <div className="recovery-card">
              <span>Confidence</span>

              <strong>
                {recommendation.confidence !== undefined
                  ? `${(
                      recommendation.confidence * 100
                    ).toFixed(1)}%`
                  : "—"}
              </strong>
            </div>
          </div>

          <div className="recovery-actions">
            <button
              type="button"
              onClick={approveRecovery}
              disabled={
                actionLoading ||
                loading
              }
            >
              {actionLoading
                ? "Processing..."
                : "Approve Recovery"}
            </button>

            <button
              type="button"
              onClick={executeRecovery}
              disabled={
                actionLoading ||
                loading
              }
            >
              {actionLoading
                ? "Processing..."
                : "Execute Recovery"}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}