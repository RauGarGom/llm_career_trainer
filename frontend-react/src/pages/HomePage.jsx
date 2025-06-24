import React from 'react';
import Navbar from '../components/Navbar';

const HomePage = () => {
  return (
    <>
      <Navbar />
      <div className="page-banner home-banner">
        <div className="container h-100">
          <div className="row align-items-center h-100">
            <div className="col-lg-6 py-3 wow fadeInUp">
              <h1 className="mb-4">Welcome to DSTrainer 2.2!</h1>
              <p className="text-lg mb-5">This application helps you practice Data Structures and Algorithms questions. Click the button below to generate a new question.</p>
              <a href="/generate-question" className="btn btn-primary btn-shadow btn-lg">Generate Question</a>
            </div>
            <div className="col-lg-6 py-3 wow zoomIn">
              <div className="img-place">
                <img src="/img/bg_image_1.png" alt="Background Image" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default HomePage;
