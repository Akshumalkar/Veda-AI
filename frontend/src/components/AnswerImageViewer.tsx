import { useRef, useEffect, useState } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Minus,
  Plus,
  AlertCircle,
} from 'lucide-react';

import type { AnswerPage, Region } from '../types/assessment';

type Props = {
  pages: AnswerPage[];
  regions: Region[];
  selectedQuestionNumber?: string;
};

export default function AnswerImageViewer({
  pages,
  regions,
  selectedQuestionNumber = 'Q1',
}: Props) {
  const [zoom, setZoom] = useState(1);
  const [currentPageIndex, setCurrentPageIndex] = useState(0);

  // Group answer regions by page
  const regionsByPage: Record<number, Region[]> = {};

  for (const region of regions) {
    const pageNumber = region.page || 1;

    if (!regionsByPage[pageNumber]) {
      regionsByPage[pageNumber] = [];
    }

    regionsByPage[pageNumber].push(region);
  }

  // Automatically switch to the first page containing
  // the selected answer region.
  useEffect(() => {
    if (regions.length > 0) {
      const targetPage = regions[0].page || 1;

      const pageIndex = pages.findIndex(
        (page) => page.page === targetPage
      );

      if (pageIndex !== -1) {
        setCurrentPageIndex(pageIndex);
      }
    }
  }, [regions, pages]);

  // Keep page index valid when pages change.
  useEffect(() => {
    if (
      pages.length > 0 &&
      currentPageIndex >= pages.length
    ) {
      setCurrentPageIndex(0);
    }
  }, [pages, currentPageIndex]);

  if (!pages || pages.length === 0) {
    return (
      <div className="figma-answer-sheet-container">
        <div className="sheet-top-dark-bar">
          <div className="sheet-title-text">
            Answer Sheet
          </div>
        </div>

        <div className="sheet-scroll-viewport">
          <div className="empty-sheet-msg">
            No answer sheet pages available for this student.
          </div>
        </div>
      </div>
    );
  }

  const activePage =
    pages[currentPageIndex] || pages[0];

  const activeRegions =
    regionsByPage[activePage.page] || [];

  return (
    <div className="figma-answer-sheet-container">
      {/* Toolbar */}
      <div className="sheet-top-dark-bar">
        <div className="sheet-title-text">
          Answer Sheet — Page {activePage.page} of {pages.length}
        </div>

        <div className="sheet-toolbar-controls">

          {/* Zoom */}
          <div className="dark-pill-btn zoom-pill">
            <button
              type="button"
              title="Zoom out"
              onClick={() =>
                setZoom((z) =>
                  Math.max(
                    0.6,
                    +(z - 0.15).toFixed(2)
                  )
                )
              }
            >
              <Minus size={13} />
            </button>

            <span className="zoom-text">
              {Math.round(zoom * 100)}%
            </span>

            <button
              type="button"
              title="Zoom in"
              onClick={() =>
                setZoom((z) =>
                  Math.min(
                    2.2,
                    +(z + 0.15).toFixed(2)
                  )
                )
              }
            >
              <Plus size={13} />
            </button>
          </div>

          {/* Page navigation */}
          {pages.length > 1 && (
            <div className="dark-pill-btn page-pill">
              <button
                type="button"
                title="Previous page"
                disabled={currentPageIndex === 0}
                onClick={() =>
                  setCurrentPageIndex((index) =>
                    Math.max(0, index - 1)
                  )
                }
              >
                <ChevronLeft size={14} />
              </button>

              <span className="page-text">
                {activePage.page} / {pages.length}
              </span>

              <button
                type="button"
                title="Next page"
                disabled={
                  currentPageIndex === pages.length - 1
                }
                onClick={() =>
                  setCurrentPageIndex((index) =>
                    Math.min(
                      pages.length - 1,
                      index + 1
                    )
                  )
                }
              >
                <ChevronRight size={14} />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Answer sheet */}
      <div className="sheet-scroll-viewport">
        <div
          className="sheet-transform-wrap"
          style={{
            transform: `scale(${zoom})`,
            transformOrigin: 'top center',
          }}
        >
          <PageCanvas
            page={activePage}
            regions={activeRegions}
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
  const highlightRef =
    useRef<HTMLDivElement>(null);

  // Scroll to selected answer region
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
    : `data:image/jpeg;base64,${page.image}`;

  const formattedQBadge =
    questionNumber.startsWith('Q') ||
    questionNumber.startsWith('q')
      ? questionNumber.toUpperCase()
      : `Q${questionNumber}`;

  return (
    <div className="figma-sheet-canvas-wrapper">

      {/* Unanswered state */}
      {regions.length === 0 && (
        <div className="unanswered-sheet-banner">
          <AlertCircle size={15} />
          <span>
            {formattedQBadge}: Question not attempted
            on this student's sheet
          </span>
        </div>
      )}

      <div
        className="sheet-image-box"
        style={{
          position: 'relative',
          width: '100%',
        }}
      >
        <img
          src={src}
          alt={`Answer sheet page ${page.page}`}
          className="sheet-paper-img"
          style={{
            display: 'block',
            width: '100%',
            height: 'auto',
          }}
        />

        {/* Exact answer regions */}
        {regions.map((region, index) => {
          /*
           * Backend coordinates are normalized 0–1000.
           *
           * Convert every coordinate to CSS percentage:
           *
           * 118  -> 11.8%
           * 450  -> 45.0%
           * 677  -> 67.7%
           * 62   -> 6.2%
           */
          const leftPercent =
            (region.bbox.x / 1000) * 100;

          const topPercent =
            (region.bbox.y / 1000) * 100;

          const widthPercent =
            (region.bbox.width / 1000) * 100;

          const heightPercent =
            (region.bbox.height / 1000) * 100;

          // Keep the box safely inside the page.
          const left = Math.max(
            0,
            Math.min(100, leftPercent)
          );

          const top = Math.max(
            0,
            Math.min(100, topPercent)
          );

          const width = Math.max(
            0.5,
            Math.min(100 - left, widthPercent)
          );

          const height = Math.max(
            0.5,
            Math.min(100 - top, heightPercent)
          );

          return (
            <div
              key={`${region.page}-${index}`}
              ref={
                index === 0
                  ? highlightRef
                  : undefined
              }
              className="figma-green-highlight-box"
              style={{
                position: 'absolute',
                left: `${left}%`,
                top: `${top}%`,
                width: `${width}%`,
                height: `${height}%`,
                display: 'block',
                pointerEvents: 'none',
                boxSizing: 'border-box',
              }}
            >
              <div className="q-badge-tab">
                {formattedQBadge}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}