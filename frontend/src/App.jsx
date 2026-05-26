import { BrowserRouter, Routes, Route } from "react-router-dom"
import Home from "./pages/Home"
import Room from "./pages/Room"
import Log from "./pages/Log"
import Multitracker from "./pages/Multitracker"
import Sphere from "./pages/Sphere"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/room" element={<Room />} />
        <Route path="/log" element={<Log />} />
        <Route path="/multitracker" element={<Multitracker />} />
        <Route path="/spheres" element={<Sphere />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
