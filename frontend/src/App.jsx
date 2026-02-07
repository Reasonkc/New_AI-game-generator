import React from 'react'
import HomePage from './HomePage'
import {Routes, Route } from "react-router";
import Create from './Create'
import GamePage from './Game';
import Navbar from './Navbar';
function App() {
  return (
    <div>
      <Navbar />
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/create" element={<Create />} />
      <Route path="/game/:gameId" element={<GamePage />} />
    </Routes>
    </div>
  )
}

export default App
