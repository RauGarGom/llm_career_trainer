import React from 'react';
import { Link } from 'react-router-dom';

function NavigationBar() {
  return (
    <nav className="navbar navbar-expand-lg navbar-light navbar-float">
      <div className="container">
        <Link to="/" className="navbar-brand">
          DS<span className="text-primary">Trainer </span><span className="text-xs">2.2</span>
        </Link>
        <button
          className="navbar-toggler"
          type="button"
          data-toggle="collapse"
          data-target="#navbarContent"
          aria-controls="navbarContent"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="collapse navbar-collapse" id="navbarContent">
          <ul className="navbar-nav ml-lg-4 pt-3 pt-lg-0">
            <li className="nav-item active">
              <Link to="/" className="nav-link">Home</Link>
            </li>
            <li className="nav-item">
              <Link to="/generate-question" className="nav-link">Train</Link>
            </li>
          </ul>
          <div className="ml-auto">
            <a
              href="https://github.com/RauGarGom/"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-outline rounded-pill"
            >
              Check out my GitHub
            </a>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default NavigationBar;
