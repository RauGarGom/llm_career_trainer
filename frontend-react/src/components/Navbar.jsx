import React from 'react';

const Navbar = () => {
  return (
    <nav className="navbar navbar-expand-lg navbar-light bg-white sticky" data-offset="500">
      <div className="container">
        <a href="/" className="navbar-brand">DS<span className="text-primary">Trainer</span> 2.2</a>

        <button className="navbar-toggler" data-toggle="collapse" data-target="#navbarContent" aria-controls="navbarContent" aria-expanded="false" aria-label="Toggle navigation">
          <span className="navbar-toggler-icon"></span>
        </button>

        <div className="navbar-collapse collapse" id="navbarContent">
          <ul className="navbar-nav ml-auto">
            <li className="nav-item active">
              <a className="nav-link" href="/">Home</a>
            </li>
            <li className="nav-item">
              <a className="nav-link" href="/generate-question">Train</a>
            </li>
            <li className="nav-item">
              <a className="btn btn-primary ml-lg-2" href="https://github.com/ClimbsRocks/DSTrainer" target="_blank" rel="noopener noreferrer">Check out my GitHub</a>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
