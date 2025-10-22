// src/App.js

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Sayfalarımızı import ediyoruz
import LoginPage from './pages/LoginPage';
import BranchListPage from './pages/BranchListPage';
import UserListPage from './pages/UserListPage';
import AvailabilityPage from './pages/AvailabilityPage';
import TakvimPage from './pages/TakvimPage';
import IsteklerimPage from './pages/IsteklerimPage';

// Bileşenlerimizi import ediyoruz
import Navbar from './components/Navbar';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        {/* Navbar, Rotaların dışında olmalı ki her sayfada görünsün */}
        <Navbar />

        <main>
          {/* Routes bloğunun içinde SADECE Route bileşenleri olmalı */}
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/subeler" element={<BranchListPage />} />
            <Route path="/kullanicilar" element={<UserListPage />} />
            <Route path="/musaitlik" element={<AvailabilityPage />} />
            <Route path="/takvim" element={<TakvimPage />} />
            <Route path="/isteklerim" element={<IsteklerimPage />} />
            
            {/* Ana sayfa / olduğunda kullanıcıyı otomatik olarak /login'e yönlendir */}
            <Route path="/" element={<Navigate replace to="/login" />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;