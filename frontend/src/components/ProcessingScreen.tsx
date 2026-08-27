export default function ProcessingScreen() {
  return (
    <div className="figma-extracting-fullscreen">
      <div className="extracting-spinner-container">
        <div className="extracting-rolling-circle">
          <svg viewBox="0 0 64 64" width="72" height="72" className="rolling-spinner-svg">
            <circle
              className="rolling-spinner-bg"
              cx="32"
              cy="32"
              r="26"
              fill="none"
              stroke="#FFE8DE"
              strokeWidth="5"
            />
            <circle
              className="rolling-spinner-circle"
              cx="32"
              cy="32"
              r="26"
              fill="none"
              stroke="#FF6B35"
              strokeWidth="5"
              strokeDasharray="120 50"
              strokeLinecap="round"
            />
          </svg>
        </div>
      </div>

      <h2 className="extracting-main-text">Extracting...</h2>
      <p className="extracting-sub-text">This may take a while</p>
    </div>
  );
}

