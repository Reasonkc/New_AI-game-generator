import React from 'react'
import HomePage from './HomePage'
import {Routes, Route } from "react-router";
import Create from './Create'
import GamePage from './Game';
import Navbar from './Navbar';
import PrivacyPolicy from './PrivacyPolicy';
import Gallery from './Gallery';
import ErrorBoundary from './components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
    <div>
      <Navbar />
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/create" element={<Create />} />
      <Route path="/game/:gameId" element={<GamePage />} />
      <Route path="/privacy" element={<PrivacyPolicy />} />
      <Route path="/gallery" element={<Gallery />} />
    </Routes>
    </div>
    </ErrorBoundary>
  )
}

export default App
