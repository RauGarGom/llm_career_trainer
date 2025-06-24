import React from 'react';
import { Link } from 'react-router-dom';
import NavigationBar from '../components/NavigationBar';

function EvaluationPage() {
  const previousAnswer = "This was my previous answer to the main question. I discussed various aspects and provided examples.";
  const followupQuestion = "Can you elaborate on the second point you made regarding performance implications?";
  const grade = "A-";
  const interviewerThoughts = "The candidate has a good grasp of the main concepts but needs to be more specific when discussing performance. The follow-up aims to test this depth.";

  // Basic inline styles for two-column layout using flexbox
  const pageStyles = {
    display: 'flex',
    padding: '20px',
    gap: '30px', // Space between columns
  };

  const columnStyles = {
    flex: 1, // Each column takes equal width
    verticalAlign: 'top',
  };

  const leftColumnStyles = {
    flex: 2, // Left column takes 2/3 of the width
    verticalAlign: 'top',
    paddingRight: '30px',
  };

  const rightColumnStyles = {
    flex: 1, // Right column takes 1/3 of the width
    verticalAlign: 'top',
  };


  return (
    <>
      <NavigationBar />
      <div className="page-section"> {/* Corresponds to original evaluation.html structure */}
        <div className="container pt-5"> {/* Container from original */}
          <div style={{ display: 'flex', width: '100%' }}> {/* Flex container for columns */}
            {/* Left Column */}
            <div style={leftColumnStyles}>
              <div> {/* id="answer" equivalent */}
                <h3 className="title-section">Your Answer:</h3>
                <p className="text-lg">{previousAnswer}</p>
              </div>

              <div className="mt-4"> {/* id="follow_up" equivalent, mt-4 for spacing */}
                <h3 className="title-section">Follow-up:</h3>
                <p className="text-lg">{followupQuestion}</p>
                <textarea
                  rows="6"
                  name="follow_up_answer"
                  className="form-control"
                  placeholder="Enter your answer to the follow-up here"
                  cols="50"
                ></textarea>
                <div className="button-group d-flex justify-content-start mt-4">
                  <button type="button" className="btn btn-primary rounded-pill mr-2">
                    Submit Answer
                  </button>
                  <button type="button" className="btn btn-outline rounded-pill mr-2">
                    Explain this question
                  </button>
                  <Link to="/generate-question" className="btn btn-outline rounded-pill">
                    Generate Another Question
                  </Link>
                </div>
              </div>
            </div>

            {/* Right Column */}
            <div style={rightColumnStyles}> {/* id="sidebar" equivalent */}
              <div> {/* id="grade" equivalent */}
                <h3 className="title-section">Your grade</h3>
                <h4 className="subhead">{grade}</h4>
              </div>
              <div style={{ paddingTop: '50px' }}> {/* id="thought" equivalent */}
                <h3 className="title-section">The interviewer thinks...</h3>
                <p>{interviewerThoughts}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default EvaluationPage;
