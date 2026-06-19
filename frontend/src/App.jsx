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
          <Route path="/room/:roomId" element={<Room />} />
          <Route path="/log/:roomId" element={<Log />} />
          <Route path="/multitracker/:roomId" element={<Multitracker />} />
          <Route path="/spheres/:roomId" element={<Sphere />} />
          <Route path="/tracker/:roomId/:slot" element={<Tracker />} />
          <Route path="/login" element={<Login />} />
        </Routes>
      </BrowserRouter>
    </UserProvider>
  )
}

export default App
