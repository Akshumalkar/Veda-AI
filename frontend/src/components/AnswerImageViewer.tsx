import { useRef, useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, Minus, Plus, AlertCircle } from 'lucide-react';
import type { AnswerPage, Region } from '../types/assessment';

type Props = {
  pages: AnswerPage[];
  regions: Region[];
  selectedQuestionNumber?: string;
};

export default function AnswerImageViewer({ pages, regions, selectedQuestionNumber = 'Q1' }: Props) {
  const [zoom, setZoom] = useState(1);
  const [currentPageIndex, setCurrentPageIndex] = useState(0);

  // Group regions by page
  const regionsByPage: Record<number, Region[]> = {};
  for (const region of regions) {
    const p = region.page || 1;
    if (!regionsByPage[p]) regionsByPage[p] = [];
    regionsByPage[p].push(region);
  }

  // Auto-switch to the page where this answer appears
  useEffect(() => {
    if (regions && regions.length > 0) {
      const targetPage = regions[0].page || 1;
      const idx = pages.findIndex((p) => p.page === targetPage);
      if (idx !== -1) {
        setCurrentPageIndex(idx);
      }
    }
  }, [regions, pages]);

  // If pages change (e.g. switching between students with different page counts), ensure valid index
  useEffect(() => {
    if (currentPageIndex >= pages.length) {
      setCurrentPageIndex(0);
    }
  }, [pages, currentPageIndex]);

  if (!pages || pages.length === 0) {
    return (
      <div className="figma-answer-sheet-container">
        <div className="sheet-top-dark-bar">
          <div className="sheet-title-text">Answer Sheet</div>
        </div>
        <div className="sheet-scroll-viewport">
          <div className="empty-sheet-msg">No answer sheet pages available for this student.</div>
        </div>
      </div>
    );
  }

  const activePage = pages[currentPageIndex] || pages[0];

  return (
    <div className="figma-answer-sheet-container">
      {/* Dark Top Toolbar */}
      <div className="sheet-top-dark-bar">
        <div className="sheet-title-text">
          Answer Sheet — Page {activePage.page} of {pages.length}
        </div>

        <div className="sheet-toolbar-controls">
          {/* Zoom Control */}
          <div className="dark-pill-btn zoom-pill">
            <button
              onClick={() => setZoom((z) => Math.max(0.6, +(z - 0.15).toFixed(2)))}
              title="Zoom out"
              type="button"
            >
              <Minus size={13} />
            </button>
            <span className="zoom-text">{Math.round(zoom * 100)}%</span>
            <button
              onClick={() => setZoom((z) => Math.min(2.2, +(z + 0.15).toFixed(2)))}
              title="Zoom in"
              type="button"
            >
              <Plus size={13} />
            </button>
          </div>

          {/* Page Stepper */}
          {pages.length > 1 && (
            <div className="dark-pill-btn page-pill">
              <button
                onClick={() => setCurrentPageIndex((idx) => Math.max(0, idx - 1))}
                disabled={currentPageIndex === 0}
                title="Previous page"
                type="button"
              >
                <ChevronLeft size={14} />
              </button>
              <span className="page-text">
                {activePage.page} / {pages.length}
              </span>
              <button
                onClick={() => setCurrentPageIndex((idx) => Math.min(pages.length - 1, idx + 1))}
                disabled={currentPageIndex === pages.length - 1}
                title="Next page"
                type="button"
              >
                <ChevronRight size={14} />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Answer Sheet Image with Live Green Bounding Box */}
      <div className="sheet-scroll-viewport">
        <div
          className="sheet-transform-wrap"
          style={{ transform: `scale(${zoom})`, transformOrigin: 'top center' }}
        >
          <PageCanvas
            page={activePage}
            regions={regionsByPage[activePage.page] || []}
            questionNumber={selectedQuestionNumber}
          />
        </div>
      </div>
    </div>
  );
}

function PageCanvas({
  page,
  regions,
  questionNumber,
}: {
  page: AnswerPage;
  regions: Region[];
  questionNumber: string;
}) {
  const highlightRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (highlightRef.current) {
      highlightRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
    }
  }, [regions, page]);

  const src = page.image.startsWith('data:')
    ? page.image
    : 'data:image/jpeg;base64,' + page.image;

  const formattedQBadge = questionNumber.startsWith('Q') || questionNumber.startsWith('q')
    ? questionNumber.toUpperCase()
    : `Q${questionNumber}`;

  return (
    <div className="figma-sheet-canvas-wrapper">
      {regions.length === 0 && (
        <div className="unanswered-sheet-banner">
          <AlertCircle size={15} />
          <span>{formattedQBadge}: Question not attempted on this student's sheet</span>
        </div>
      )}

      <div className="sheet-image-box">
        <img
          src={src}
          alt={`Answer sheet page ${page.page}`}
          className="sheet-paper-img"
        />

        {/* Green Highlight Box with Percentage Positioning */}
        {regions.map((region, idx) => {
          // Normalize coordinate conversion from [0..1000] to percentage
          const rawX = region.bbox.x > 100 ? region.bbox.x / 10 : region.bbox.x;
          const rawY = region.bbox.y > 100 ? region.bbox.y / 10 : region.bbox.y;
          const rawW = region.bbox.width > 100 ? region.bbox.width / 10 : region.bbox.width;
          const rawH = region.bbox.height > 100 ? region.bbox.height / 10 : region.bbox.height;

          const left = `${Math.max(0, Math.min(96, rawX)).toFixed(2)}%`;
          const top = `${Math.max(0, Math.min(96, rawY)).toFixed(2)}%`;
          const width = `${Math.max(4, Math.min(100 - rawX, rawW)).toFixed(2)}%`;
          const height = `${Math.max(3, Math.min(100 - rawY, rawH)).toFixed(2)}%`;

          return (
            <div
              key={idx}
              ref={idx === 0 ? highlightRef : undefined}
              className="figma-green-highlight-box"
              style={{
                left,
                top,
                width,
                height,
                position: 'absolute',
                display: 'block'
              }}
            >
              {/* Green badge tab on top-left of box (e.g. Q2) */}
              <div className="q-badge-tab">{formattedQBadge}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
