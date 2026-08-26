import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

import type { AssessmentResult } from './types/assessment';
import { DEFAULT_USER, type TeacherUser } from './types/user';

import Sidebar from './components/Sidebar';
import TopHeader from './components/TopHeader';
import HomeDashboard from './components/HomeDashboard';
import ClassroomView from './components/ClassroomView';
import AssignmentsDashboard from './components/AssignmentsDashboard';
import UploadView from './components/UploadView';
import ProcessingScreen from './components/ProcessingScreen';
import ResultsView from './components/ResultsView';
import LessonStudio from './components/LessonStudio';
import SettingsView from './components/SettingsView';

import { HelpModal, ToolkitModal } from './components/Modals';

import { notificationStore } from './data/notificationStore';

import { processAssessment } from './services/api';




export default function App() {

  // =========================================================
  // USER
  // =========================================================

  const [user, setUser] = useState<TeacherUser>(() => {

    try {

      const stored = localStorage.getItem(
        'veda_educator_user'
      );

      if (stored) {

        const parsed = JSON.parse(stored);

        if (parsed.name === 'Madhur Rastogi') {
          return DEFAULT_USER;
        }

        return parsed;
      }

      return DEFAULT_USER;

    } catch {

      return DEFAULT_USER;

    }

  });


  // =========================================================
  // NAVIGATION
  // =========================================================

  const [activeTab, setActiveTab] = useState('exams');

  const [sidebarCollapsed, setSidebarCollapsed] =
    useState(false);


  // =========================================================
  // ASSESSMENT STATE
  // =========================================================

  const [questionFile, setQuestionFile] =
    useState<File | null>(null);

  const [answerFiles, setAnswerFiles] =
    useState<File[]>([]);

  const [studentNames, setStudentNames] =
    useState<string[]>([]);

  const [loading, setLoading] =
    useState(false);

  const [result, setResult] =
    useState<AssessmentResult | null>(null);

  const [error, setError] =
    useState('');


  // =========================================================
  // MODALS
  // =========================================================

  const [isHelpOpen, setIsHelpOpen] =
    useState(false);

  const [isToolkitOpen, setIsToolkitOpen] =
    useState(false);

  const [isNotifOpen, setIsNotifOpen] =
    useState(false);

  const [isProfileOpen, setIsProfileOpen] =
    useState(false);


  // =========================================================
  // SAVE USER
  // =========================================================

  useEffect(() => {

    if (user) {

      localStorage.setItem(
        'veda_educator_user',
        JSON.stringify(user)
      );

    }

  }, [user]);


  // =========================================================
  // COLLAPSE SIDEBAR DURING PROCESSING / RESULTS
  // =========================================================

  useEffect(() => {

    if (loading || result) {

      setSidebarCollapsed(true);

    }

  }, [loading, result]);


  // =========================================================
  // ANALYZE ASSESSMENT
  // =========================================================

  const handleAnalyze = async () => {

    // -------------------------------------------------------
    // Validate question paper
    // -------------------------------------------------------

    if (!questionFile) {

      setError(
        'Please upload a question paper.'
      );

      return;

    }


    // -------------------------------------------------------
    // Validate answer sheet
    // -------------------------------------------------------

    if (answerFiles.length === 0) {

      setError(
        'Please upload at least one student answer sheet.'
      );

      return;

    }


    try {

      setLoading(true);

      setError('');

      setResult(null);


      // -----------------------------------------------------
      // Call backend API
      // -----------------------------------------------------

      const data = await processAssessment({

        questionFile,

        answerFiles,

        studentNames,

      });


      // -----------------------------------------------------
      // Save result
      // -----------------------------------------------------

      setResult(data);


      // -----------------------------------------------------
      // Notification
      // -----------------------------------------------------

      const count = data.students?.length ?? 1;

      const topScorer =
        data.students?.[0]?.student_name ??
        data.student_name ??
        'Student';

      const topScore =
        data.students?.[0]?.total_score ??
        data.total_score ??
        0;

      const topMaxScore =
        data.students?.[0]?.max_score ??
        data.max_score ??
        0;

      notificationStore.addNotification({
        title: 'Assessment Grading Complete',
        message:
          `Evaluated ${count} student answer sheet` +
          `${count > 1 ? 's' : ''}. ` +
          `Score: ${topScorer} (${topScore}/${topMaxScore}).`,
        type: 'success',
        targetTab: 'exams',
      });


    } catch (err) {

      console.error(
        'Assessment processing error:',
        err
      );


      // -----------------------------------------------------
      // Axios error
      // -----------------------------------------------------

      if (axios.isAxiosError(err)) {

        const detail =
          err.response?.data?.detail;


        // Backend may return string
        if (typeof detail === 'string') {

          setError(detail);

        }

        // Backend may return:
        // {
        //   success: false,
        //   error: {
        //      message: "..."
        //   }
        // }

        else if (
          detail &&
          typeof detail === 'object'
        ) {

          const errorObject =
            detail as {
              message?: unknown;
              error?: {
                message?: unknown;
              };
            };


          if (
            errorObject.error &&
            typeof errorObject.error === 'object' &&
            errorObject.error.message
          ) {

            setError(
              String(
                errorObject.error.message
              )
            );

          }

          else if (
            errorObject.message
          ) {

            setError(
              String(
                errorObject.message
              )
            );

          }

          else {

            setError(
              'Failed to process assessment. Please try again.'
            );

          }

        }

        else {

          setError(
            'Failed to process assessment. Please try again.'
          );

        }

      }

      // -----------------------------------------------------
      // Unknown error
      // -----------------------------------------------------

      else {

        setError(
          'Failed to process assessment. Please try again.'
        );

      }

    } finally {

      setLoading(false);

    }

  };


  // =========================================================
  // RESET
  // =========================================================

  const handleReset = () => {

    setQuestionFile(null);

    setAnswerFiles([]);

    setStudentNames([]);

    setResult(null);

    setError('');

    setActiveTab('exams');

    setSidebarCollapsed(false);

  };


  // =========================================================
  // SIGN OUT
  // =========================================================

  const handleSignOut = () => {

    setUser(DEFAULT_USER);

    handleReset();

    setIsProfileOpen(false);

  };


  // =========================================================
  // CLOSE DROPDOWNS
  // =========================================================

  useEffect(() => {

    const handleDocumentClick = () => {

      setIsNotifOpen(false);

      setIsProfileOpen(false);

    };


    window.addEventListener(
      'click',
      handleDocumentClick
    );


    return () => {

      window.removeEventListener(
        'click',
        handleDocumentClick
      );

    };

  }, []);


  // =========================================================
  // UI
  // =========================================================

  return (

    <div className="veda-layout">


      {/* ===================================================
          SIDEBAR
      =================================================== */}

      <Sidebar

        activeTab={activeTab}

        onSelectTab={(tab) => {

          setActiveTab(tab);

        }}

        onOpenToolkit={() => {

          setIsToolkitOpen(true);

        }}

        collapsed={sidebarCollapsed}

        onToggleCollapse={() => {

          setSidebarCollapsed(
            !sidebarCollapsed
          );

        }}

        school={user.school}

      />


      {/* ===================================================
          MAIN CONTENT
      =================================================== */}

      <div className="veda-main-content">


        {/* =================================================
            HEADER
        ================================================= */}

        <TopHeader

          activeTab={activeTab}

          onSelectTab={setActiveTab}

          showBack={
            !!result &&
            activeTab === 'exams'
          }

          onBack={handleReset}

          onReset={handleReset}

          onOpenHelp={() => {

            setIsHelpOpen(true);

          }}

          onOpenNotifications={() => {

            setIsProfileOpen(false);

            setIsNotifOpen(
              !isNotifOpen
            );

          }}

          onOpenToolkit={() => {

            setIsToolkitOpen(true);

          }}

          onToggleProfile={() => {

            setIsNotifOpen(false);

            setIsProfileOpen(
              !isProfileOpen
            );

          }}

          isProfileOpen={isProfileOpen}

          isNotifOpen={isNotifOpen}

          user={user}

          onSignOut={handleSignOut}

          onOpenSettings={() => {

            setIsProfileOpen(false);

            setActiveTab('settings');

          }}

        />


        {/* =================================================
            BODY
        ================================================= */}

        <main className="veda-body">


          {/* =================================================
              HOME
          ================================================= */}

          {activeTab === 'home' ? (

            <HomeDashboard

              user={user}

              onGoToExams={() => {

                setActiveTab('exams');

              }}

              onGoToAssignments={() => {

                setActiveTab('assignments');

              }}

              onGoToClassroom={() => {

                setActiveTab('classroom');

              }}

            />

          )


          /* =================================================
             CLASSROOM
          ================================================= */

          : activeTab === 'classroom' ? (

            <ClassroomView

              user={user}

              onEvaluateStudentSheet={() => {

                setActiveTab('exams');

              }}

            />

          )


          /* =================================================
             ASSIGNMENTS
          ================================================= */

          : activeTab === 'assignments' ? (

            <AssignmentsDashboard

              batchSummary={
                result?.batch_summary
              }

              onOpenExamUpload={() => {

                setActiveTab('exams');

              }}

            />

          )


          /* =================================================
             LIBRARY
          ================================================= */

          : activeTab === 'library' ? (

            <LessonStudio
              user={user}
            />

          )


          /* =================================================
             SETTINGS
          ================================================= */

          : activeTab === 'settings' ? (

            <SettingsView

              user={user}

              onUpdateUser={(updated) => {

                setUser(updated);

              }}

            />

          )


          /* =================================================
             PROCESSING
          ================================================= */

          : loading ? (

            <ProcessingScreen />

          )


          /* =================================================
             RESULTS
          ================================================= */

          : result ? (

            <ResultsView

              result={result}

              school={user.school}

              onReset={handleReset}

            />

          )


          /* =================================================
             UPLOAD
          ================================================= */

          : (

            <UploadView

              questionFile={questionFile}

              answerFiles={answerFiles}

              studentNames={studentNames}


              setQuestionFile={(file) => {

                setQuestionFile(file);

                if (error) {

                  setError('');

                }

              }}


              setAnswerFiles={(files) => {

                setAnswerFiles(files);

                if (error) {

                  setError('');

                }

              }}


              setStudentNames={
                setStudentNames
              }


              onAnalyze={
                handleAnalyze
              }


              loading={loading}

              error={error}

            />

          )}

        </main>

      </div>


      {/* ===================================================
          HELP MODAL
      =================================================== */}

      {isHelpOpen && (

        <HelpModal

          onClose={() => {

            setIsHelpOpen(false);

          }}

          onOpenExams={() => {

            setIsHelpOpen(false);

            setActiveTab('exams');

          }}

          onOpenStudio={() => {

            setIsHelpOpen(false);

            setActiveTab('library');

          }}

        />

      )}


      {/* ===================================================
          TOOLKIT MODAL
      =================================================== */}

      {isToolkitOpen && (

        <ToolkitModal

          onClose={() => {

            setIsToolkitOpen(false);

          }}

          onGoToExams={() => {

            setActiveTab('exams');

          }}

          onGoToLibrary={() => {

            setActiveTab('library');

          }}

          onGoToAssignments={() => {

            setActiveTab('assignments');

          }}

          onGoToClassroom={() => {

            setActiveTab('classroom');

          }}

          onGoToSettings={() => {

            setActiveTab('settings');

          }}

        />

      )}

    </div>

  );

}