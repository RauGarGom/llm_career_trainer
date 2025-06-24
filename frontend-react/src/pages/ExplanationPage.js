import React from 'react';
import NavigationBar from '../components/NavigationBar';

function ExplanationPage() {
  const placeholderQuestion = "What is the difference between a List and a Tuple in Python?";
  const placeholderExplanation = "Explanation will appear here...";

  return (
    <>
      <NavigationBar />
      <div className="page-section">
        <div className="container pt-5">
          <div className="row">
            <div className="col-lg-8">
              <h3 className="title-section">Question:</h3>
              <p className="text-lg">{placeholderQuestion}</p>

              <h3 className="title-section mt-4">Explanation:</h3>
              <div id="explanation" className="text-lg" style={{ minHeight: '200px' }}>
                {placeholderExplanation}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default ExplanationPage;
