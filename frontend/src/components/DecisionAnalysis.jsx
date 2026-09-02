import { useState } from "react";
import { api } from "../services/api";

function formatValue(value) {
  if (value === null || value === undefined) {
    return "—";
  }

  if (typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }

  return String(value);
}

export default function DecisionAnalysis() {
  const [paymentId, setPaymentId] = useState("");

  const [decision, setDecision] = useState(null);
  const [counterfactual, setCounterfactual] = useState(null);

  const [loadingDecision, setLoadingDecision] =
    useState(false);

  const [loadingCounterfactual, setLoadingCounterfactual] =
    useState(false);

  const [error, setError] = useState("");

  const runAdaptiveDecision = async () => {
    const id = paymentId.trim();

    if (!id) {
      setError("Enter a payment ID first.");
      return;
    }

    try {
      setLoadingDecision(true);
      setError("");
      setDecision(null);

      const data = await api.getAdaptiveDecision(id);

      setDecision(data);
    } catch (err) {
      console.error("Adaptive decision failed:", err);

      setError(
        err.message ||
          "Unable to generate adaptive decision."
      );
    } finally {
      setLoadingDecision(false);
    }
  };

  const runCounterfactual = async () => {
    const id = paymentId.trim();

    if (!id) {
      setError("Enter a payment ID first.");
      return;
    }

    try {
      setLoadingCounterfactual(true);
      setError("");
      setCounterfactual(null);

      const data = await api.getCounterfactual(id);

      setCounterfactual(data);
    } catch (err) {
      console.error(
        "Counterfactual analysis failed:",
        err
      );

      setError(
        err.message ||
          "Unable to generate counterfactual analysis."
      );
    } finally {
      setLoadingCounterfactual(false);
    }
  };

  return (
    <section className="decision-analysis">
      <div className="section-header">
        <div>
          <h2>AI Decision Intelligence</h2>

          <p>
            Compare adaptive recovery decisions and
            alternative recovery outcomes.
          </p>
        </div>
      </div>

      <div className="decision-search">
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
          onClick={runAdaptiveDecision}
          disabled={
            loadingDecision ||
            loadingCounterfactual
          }
        >
          {loadingDecision
            ? "Analyzing..."
            : "Run Adaptive Decision"}
        </button>

        <button
          type="button"
          onClick={runCounterfactual}
          disabled={
            loadingDecision ||
            loadingCounterfactual
          }
        >
          {loadingCounterfactual
            ? "Simulating..."
            : "Run Counterfactual"}
        </button>
      </div>

      {error && (
        <div className="decision-error">
          {error}
        </div>
      )}

      {decision && (
        <div className="analysis-result">
          <h3>Adaptive Decision Result</h3>

          <div className="analysis-grid">
            {Object.entries(decision).map(
              ([key, value]) => (
                <div
                  className="analysis-card"
                  key={key}
                >
                  <span>
                    {key
                      .replace(/_/g, " ")
                      .replace(/\b\w/g, (char) =>
                        char.toUpperCase()
                      )}
                  </span>

                  <strong>
                    {typeof value === "object"
                      ? "Structured Result"
                      : formatValue(value)}
                  </strong>

                  {typeof value === "object" && (
                    <pre>
                      {formatValue(value)}
                    </pre>
                  )}
                </div>
              )
            )}
          </div>
        </div>
      )}

      {counterfactual && (
        <div className="analysis-result">
          <h3>Counterfactual Analysis</h3>

          <div className="analysis-grid">
            {Object.entries(counterfactual).map(
              ([key, value]) => (
                <div
                  className="analysis-card"
                  key={key}
                >
                  <span>
                    {key
                      .replace(/_/g, " ")
                      .replace(/\b\w/g, (char) =>
                        char.toUpperCase()
                      )}
                  </span>

                  <strong>
                    {typeof value === "object"
                      ? "Alternative Scenario"
                      : formatValue(value)}
                  </strong>

                  {typeof value === "object" && (
                    <pre>
                      {formatValue(value)}
                    </pre>
                  )}
                </div>
              )
            )}
          </div>
        </div>
      )}
    </section>
  );
}