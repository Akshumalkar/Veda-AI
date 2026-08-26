export default function ProcessingScreen() {
  return (
    <div className="figma-extracting-fullscreen">
      <div className="extracting-sparkle-center">
        <svg viewBox="0 0 120 120" width="96" height="96" fill="none" xmlns="http://www.w3.org/2000/svg">
          {/* Main big 4-point sparkle */}
          <path
            d="M60 12 C60 40 68 52 96 60 C68 68 60 80 60 108 C60 80 52 68 24 60 C52 52 60 40 60 12 Z"
            fill="#FF6B35"
            className="sparkle-primary"
          />
          {/* Top-left small sparkle */}
          <path
            d="M26 26 C26 34 29 38 38 41 C29 44 26 48 26 56 C26 48 23 44 14 41 C23 38 26 34 26 26 Z"
            fill="#FF9E7A"
            opacity="0.85"
            className="sparkle-secondary"
          />
          {/* Bottom-right mini sparkle dot */}
          <circle cx="98" cy="88" r="4.5" fill="#FF8A5B" opacity="0.9" className="sparkle-dot" />
        </svg>
      </div>

      <h2 className="extracting-main-text">Extracting...</h2>
      <p className="extracting-sub-text">This may take a while</p>
    </div>
  );
}
