import { useRef } from 'react';
import {
  AlertCircle,
  BookOpen,
  Check,
  ChevronRight,
  FileText,
  Loader2,
  Sparkles,
  Upload,
  X,
  Plus,
  Users,
  UserCheck,
} from 'lucide-react';

type UploadViewProps = {
  questionFile: File | null;
  answerFiles: File[];
  studentNames: string[];
  selectedStudent?: any;
  setQuestionFile: (f: File | null) => void;
  setAnswerFiles: (files: File[]) => void;
  setStudentNames: (names: string[]) => void;
  onAnalyze: () => void;
  loading: boolean;
  error: string;
};

export default function UploadView({
  questionFile,
  answerFiles,
  setQuestionFile,
  setAnswerFiles,
  setStudentNames,
  onAnalyze,
  loading,
  error,
}: UploadViewProps) {
  const qRef = useRef<HTMLInputElement>(null);
  const aRef = useRef<HTMLInputElement>(null);

  /*
   * Student names are no longer entered manually.
   *
   * We still maintain the studentNames state because the backend/API
   * currently accepts student_names. Names are automatically generated
   * from the uploaded answer-sheet filename.
   */
  const createStudentNames = (files: File[]) => {
    return files.map((file, index) => {
      const filename = file.name
        .replace(/\.[^/.]+$/, '')
        .replace(/[_-]+/g, ' ')
        .trim();

      return filename || `Student ${index + 1}`;
    });
  };

  const handleAddAnswerFiles = (newFiles: FileList | null) => {
    if (!newFiles || newFiles.length === 0) return;

    const validTypes = [
      'application/pdf',
      'image/png',
      'image/jpeg',
      'image/webp',
    ];

    const valid = Array.from(newFiles).filter((file) => {
      return validTypes.includes(file.type);
    });

    if (valid.length === 0) {
      alert('Please upload PDF, PNG, JPG or WEBP files.');
      return;
    }

    const updatedFiles = [...answerFiles, ...valid];

    setAnswerFiles(updatedFiles);

    // Automatically create names from filenames.
    // No student-name input is shown to the teacher.
    setStudentNames(createStudentNames(updatedFiles));
  };

  const handleRemoveAnswerFile = (idx: number) => {
    const updatedFiles = answerFiles.filter((_, i) => i !== idx);

    setAnswerFiles(updatedFiles);
    setStudentNames(createStudentNames(updatedFiles));
  };

  const readyToEvaluate = !!questionFile && answerFiles.length > 0;

  return (
    <div className="figma-upload-viewport">
      <div className="figma-upload-content-wrap">

        {/* =====================================================
            PAGE HEADER
        ===================================================== */}

        <h1 className="figma-main-heading">
          Upload{' '}
          <span className="figma-heading-pill">
            Question Paper &amp; Student Answer Sheets
          </span>
        </h1>

        <p className="figma-sub-heading">
          Upload 1 Question Paper and one or more Student Answer Sheets
          for automated batch OCR &amp; grading
        </p>

        {/* =====================================================
            TEACHER AVATAR
        ===================================================== */}

        <div className="figma-avatar-container">
          <div className="orbit-glow-3" />
          <div className="orbit-glow-2" />

          <div className="orbit-glow-1">
            <img
              src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=160&auto=format&fit=crop&q=80"
              alt="Teacher"
              className="avatar-photo"
              onError={(e) => {
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
          </div>

          <div className="orbit-icon-dot dot-1">
            <FileText size={10} />
          </div>

          <div className="orbit-icon-dot dot-2">
            <Sparkles size={10} />
          </div>

          <div className="orbit-icon-dot dot-3">
            <BookOpen size={10} />
          </div>

          <div className="orbit-icon-dot dot-4">
            <Check size={10} />
          </div>
        </div>

        {/* =====================================================
            UPLOAD CARDS
        ===================================================== */}

        <div className="figma-cards-flex">

          {/* -------------------------------------------------
              QUESTION PAPER
          ------------------------------------------------- */}

          <div
            className="figma-upload-card-box"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();

              const file = e.dataTransfer.files?.[0];

              if (file) {
                setQuestionFile(file);
              }
            }}
          >
            {!questionFile ? (
              <button
                className="figma-upload-inner-btn"
                onClick={() => qRef.current?.click()}
                type="button"
              >
                <div className="figma-arrow-icon-wrap">
                  <Upload size={20} />
                </div>

                <div className="figma-card-label">
                  Upload{' '}
                  <span className="label-orange">
                    Question Paper
                  </span>
                </div>

                <div className="figma-card-size">
                  PDF or Image (Max 10MB)
                </div>
              </button>
            ) : (
              <div className="figma-file-attached">

                <div
                  className={
                    'pdf-red-badge ' +
                    (!questionFile.type.includes('pdf')
                      ? 'img-badge'
                      : '')
                  }
                >
                  <span>
                    {questionFile.type.includes('pdf')
                      ? 'PDF'
                      : 'IMG'}
                  </span>
                </div>

                <div className="attached-details">
                  <strong className="attached-name">
                    {questionFile.name}
                  </strong>

                  <span className="attached-sub">
                    {(questionFile.size / 1024 / 1024).toFixed(1)}
                    MB • Question Paper
                  </span>
                </div>

                <button
                  className="remove-cross-btn"
                  onClick={() => setQuestionFile(null)}
                  type="button"
                  title="Remove file"
                >
                  <X size={15} />
                </button>

              </div>
            )}

            <input
              ref={qRef}
              type="file"
              hidden
              accept=".pdf,.png,.jpg,.jpeg,.webp"
              onChange={(e) => {
                if (e.target.files?.[0]) {
                  setQuestionFile(e.target.files[0]);
                }

                e.target.value = '';
              }}
            />
          </div>

          {/* -------------------------------------------------
              ANSWER SHEETS
          ------------------------------------------------- */}

          <div
            className="figma-upload-card-box batch-upload-card"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();

              handleAddAnswerFiles(e.dataTransfer.files);
            }}
          >
            {answerFiles.length === 0 ? (
              <button
                className="figma-upload-inner-btn"
                onClick={() => aRef.current?.click()}
                type="button"
              >
                <div className="figma-arrow-icon-wrap">
                  <Users size={20} />
                </div>

                <div className="figma-card-label">
                  Upload{' '}
                  <span className="label-orange">
                    Student Answer Sheets
                  </span>
                </div>

                <div className="figma-card-size">
                  Single or Batch Upload (Select multiple)
                </div>
              </button>
            ) : (
              <div className="batch-attached-container">

                {/* Batch header */}

                <div className="batch-header-row">

                  <span className="batch-count-badge">
                    <UserCheck size={13} />

                    {answerFiles.length}{' '}
                    Answer Sheet
                    {answerFiles.length > 1 ? 's' : ''}{' '}
                    Attached
                  </span>

                  <button
                    className="add-more-sheets-btn"
                    onClick={() => aRef.current?.click()}
                    type="button"
                  >
                    <Plus size={13} />
                    Add More
                  </button>

                </div>

                {/* -------------------------------------------------
                    FILE LIST

                    Student name input intentionally removed.
                ------------------------------------------------- */}

                <div className="batch-files-scroll-list">

                  {answerFiles.map((file, idx) => (

                    <div
                      key={`${file.name}-${idx}`}
                      className="batch-file-row"
                    >

                      <div
                        className={
                          'pdf-red-badge mini ' +
                          (!file.type.includes('pdf')
                            ? 'img-badge'
                            : '')
                        }
                      >
                        <span>
                          {file.type.includes('pdf')
                            ? 'PDF'
                            : 'IMG'}
                        </span>
                      </div>

                      <div
                        className="student-name-input-col"
                        style={{
                          flex: 1,
                          minWidth: 0,
                        }}
                      >
                        <strong
                          className="attached-name"
                          title={file.name}
                          style={{
                            display: 'block',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          Answer Sheet {idx + 1}
                        </strong>

                        <span className="file-name-hint">
                          {file.name}{' '}
                          (
                          {(file.size / 1024 / 1024).toFixed(1)}
                          MB)
                        </span>
                      </div>

                      <button
                        className="remove-cross-btn mini"
                        onClick={() =>
                          handleRemoveAnswerFile(idx)
                        }
                        type="button"
                        title="Remove answer sheet"
                      >
                        <X size={13} />
                      </button>

                    </div>

                  ))}

                </div>
              </div>
            )}

            <input
              ref={aRef}
              type="file"
              hidden
              multiple
              accept=".pdf,.png,.jpg,.jpeg,.webp"
              onChange={(e) => {
                handleAddAnswerFiles(e.target.files);
                e.target.value = '';
              }}
            />

          </div>
        </div>

        {/* =====================================================
            ERROR
        ===================================================== */}

        {error && (
          <div className="figma-error-banner">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* =====================================================
            ACTION BUTTON
        ===================================================== */}

        <div className="figma-action-center">

          <button
            className={
              'figma-mapping-btn ' +
              (readyToEvaluate ? 'ready' : 'disabled')
            }
            onClick={onAnalyze}
            disabled={loading || !readyToEvaluate}
            type="button"
          >
            {loading ? (
              <>
                <Loader2
                  className="spin"
                  size={16}
                />

                Evaluating{' '}
                {answerFiles.length}{' '}
                Student Sheet
                {answerFiles.length > 1 ? 's' : ''}
                ...
              </>
            ) : (
              <>
                Start{' '}
                {answerFiles.length > 1
                  ? `Batch Grading (${answerFiles.length} Students)`
                  : 'Assessment Mapping'}

                <ChevronRight size={16} />
              </>
            )}
          </button>

          <p className="figma-action-hint">
            Deterministic question matching &amp; Gemini vision OCR
            across all uploaded student sheets
          </p>

        </div>

      </div>
    </div>
  );
}