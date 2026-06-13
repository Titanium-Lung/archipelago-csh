import { useState, useEffect } from "react"
import { BrowserRouter, Routes, Route } from "react-router-dom"
import Home from "./pages/Home"
import Room from "./pages/Room"
import Log from "./pages/Log"
import Multitracker from "./pages/Multitracker"
import Sphere from "./pages/Sphere"
import Tracker from "./pages/Tracker"
import Login from "./pages/Login"
import { UserProvider } from "./UserContext"

function App() {
  return (
    <UserProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/room" element={<Room />} />
          <Route path="/log" element={<Log />} />
          <Route path="/multitracker" element={<Multitracker />} />
          <Route path="/spheres" element={<Sphere />} />
          <Route path="/tracker/:slot" element={<Tracker />} />
          <Route path="/login" element={<Login />} />
        </Routes>
      </BrowserRouter>
    </UserProvider>
  )
}

export default App
