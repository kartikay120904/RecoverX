import { useEffect, useState } from "react";
import { api } from "../services/api";

export default function PaymentOperations() {
  const [payments, setPayments] = useState([]);
  const [search, setSearch] = useState("");
  const [limit, setLimit] = useState(10);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadPayments = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await api.getPayments({
        search,
        limit,
      });

      /*
       Supports either:
       - an array response
       - an object containing a payments array

       This prevents a simple response-shape mismatch
       from crashing the UI.
      */
      if (Array.isArray(data)) {
        setPayments(data);
      } else if (Array.isArray(data.payments)) {
        setPayments(data.payments);
      } else {
        setPayments([]);
      }
    } catch (err) {
      console.error("Failed to load payments:", err);
      setError(err.message || "Failed to load payments");
      setPayments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPayments();
  }, [limit]);

  const handleSearch = (event) => {
    event.preventDefault();
    loadPayments();
  };

  return (
    <section className="payment-operations">
      <div className="section-header">
        <div>
          <h2>Payment Operations</h2>
          <p>Monitor and investigate simulated payment activity.</p>
        </div>

        <button
          type="button"
          onClick={loadPayments}
          disabled={loading}
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <form
        className="payment-controls"
        onSubmit={handleSearch}
      >
        <input
          type="text"
          placeholder="Search payment..."
          value={search}
          onChange={(event) =>
            setSearch(event.target.value)
          }
        />

        <select
          value={limit}
          onChange={(event) =>
            setLimit(Number(event.target.value))
          }
        >
          <option value={5}>5 payments</option>
          <option value={10}>10 payments</option>
          <option value={20}>20 payments</option>
          <option value={50}>50 payments</option>
        </select>

        <button type="submit">
          Search
        </button>
      </form>

      {loading && (
        <div className="api-state">
          Loading payments...
        </div>
      )}

      {!loading && error && (
        <div className="api-state api-error">
          <p>{error}</p>

          <button
            type="button"
            onClick={loadPayments}
          >
            Retry
          </button>
        </div>
      )}

      {!loading && !error && payments.length === 0 && (
        <div className="api-state">
          No payments found.
        </div>
      )}

      {!loading && !error && payments.length > 0 && (
        <div className="payment-table-wrapper">
          <table className="payment-table">
            <thead>
              <tr>
                <th>Payment ID</th>
                <th>Status</th>
                <th>Amount</th>
                <th>Currency</th>
              </tr>
            </thead>

            <tbody>
              {payments.map((payment, index) => (
                <tr
                  key={
                    payment.payment_id ||
                    payment.id ||
                    index
                  }
                >
                  <td>
                    {payment.payment_id ||
                      payment.id ||
                      "—"}
                  </td>

                  <td>
                    {payment.status ||
                      payment.state ||
                      "Unknown"}
                  </td>

                  <td>
                    {payment.amount ??
                      "—"}
                  </td>

                  <td>
                    {payment.currency ||
                      "INR"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}