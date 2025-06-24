import React from 'react';
import { Link } from 'react-router-dom';
import NavigationBar from '../components/NavigationBar'; // Adjusted path

function HomePage() {
  return (
    <>
      <NavigationBar />
      <div className="page-banner home-banner">
        <div className="container h-100">
          <div className="row align-items-center h-100">
            <div className="col-lg-6 py-3">
              <h1 className="mb-4">Your next interview. Easier.</h1>
              <p className="text-lg mb-5">
                Learn how a technical interviewer would react to your answers, and practise for your next interview
              </p>
              <Link to="/generate-question" className="btn btn-primary btn-split ml-2">
                Generate Question <div className="fab"><span className="mai-play"></span></div>
              </Link>
            </div>
            <div className="col-lg-6 py-3">
              <div className="img-place">
                {/* Assuming assets are in public folder and served from / */}
                <img src="/assets/img/bg_image_1.png" alt="Background" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default HomePage;
