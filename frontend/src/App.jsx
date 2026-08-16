import { useState, useEffect } from "react"
import { BrowserRouter, Routes, Route } from "react-router-dom"
import Home from "./pages/Home"
import Room from "./pages/Room"
import Log from "./pages/Log"
import Multitracker from "./pages/Multitracker"
import Sphere from "./pages/Sphere"
import Tracker from "./pages/Tracker"
import Login from "./pages/Login"
import PageNotFound from "./pages/PageNotFound"
import Settings from "./pages/Settings"
import Stats from "./pages/Stats"
import { UserProvider } from "./UserContext"

function App() {
  // Set theme to light or dark 
  useEffect(() => {
    const savedTheme = localStorage.getItem("theme") || "auto"
    const html = document.documentElement
    if (savedTheme === "auto") {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches
      html.setAttribute("data-bs-theme", prefersDark ? "dark" : "light")
    } else {
      html.setAttribute("data-bs-theme", savedTheme)
    }
  }, [])

  return (
    <UserProvider> {/* Fetches user data to provide to every other component */}
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/room/:roomId" element={<Room />} />
          <Route path="/log/:roomId" element={<Log />} />
          <Route path="/multitracker/:roomId" element={<Multitracker />} />
          <Route path="/spheres/:roomId" element={<Sphere />} />
          <Route path="/tracker/:roomId/:slot" element={<Tracker />} />
          <Route path="/login" element={<Login />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/stats" element={<Stats />} />
          <Route path="*" element={<PageNotFound />} />
        </Routes>
      </BrowserRouter>
    </UserProvider>
  )
}

export default App
