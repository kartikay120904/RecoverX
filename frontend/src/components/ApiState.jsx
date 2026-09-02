export default function ApiState({
  loading,
  error,
  children,
  onRetry,
}) {
  if (loading) {
    return (
      <div className="api-state api-loading">
        Loading RecoverX data...
      </div>
    );
  }

  if (error) {
    return (
      <div className="api-state api-error">
        <p>Unable to load data.</p>

        <p className="api-error-message">
          {error}
        </p>

        {onRetry && (
          <button onClick={onRetry}>
            Retry
          </button>
        )}
      </div>
    );
  }

  return children;
}