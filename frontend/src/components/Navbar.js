// src/components/Navbar.js
import React from 'react';
import { NavLink } from 'react-router-dom';
import { FiDatabase } from 'react-icons/fi'; // Importando um ícone
import './Navbar.css';

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <FiDatabase className="brand-icon" />
        <h1>SuppBot BI</h1>
      </div>
      <div className="navbar-links">
        <NavLink to="/">Dashboard</NavLink>
        <NavLink to="/chat">Chatbot</NavLink>
      </div>
    </nav>
  );
}
export default Navbar;