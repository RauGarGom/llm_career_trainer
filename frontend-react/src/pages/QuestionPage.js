import React from 'react';
import { Link } from 'react-router-dom';
import NavigationBar from '../components/NavigationBar';

function QuestionPage() {
  const placeholderQuestion = "What is the difference between a List and a Tuple in Python?";

  return (
    <>
      <NavigationBar />
      <div className="page-section">
        <div className="container h-100">
          <p className="text-lg mt-5">{placeholderQuestion}</p>
          {/* In React, we typically handle form submissions with state and event handlers,
              so the form tags here are mostly for structure and styling if needed.
              The actual submission logic will be added later. */}
          <div> {/* Simplified structure for buttons instead of nested forms */}
            <textarea
              rows="6"
              name="answer"
              className="form-control mb-4"
              placeholder="Enter your answer here"
              cols="50"
            ></textarea>
            <div className="d-flex justify-content-start align-items-center">
              <button type="button" className="btn btn-primary rounded-pill mr-2">
                Submit Answer
              </button>
              <button type="button" className="btn btn-outline rounded-pill mr-2">
                Explain this question
              </button>
              <Link to="/generate-question" className="btn btn-outline rounded-pill ml-1">
                Generate Another Question
              </Link>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default QuestionPage;
