import { useEffect, useState } from "react"
import { useUser } from "../UserContext"
import { Navbar } from "../Navbar"

function Settings() {
    const user = useUser()
    
    const [theme, setTheme] = useState(localStorage.getItem("theme") || "auto")

    useEffect(() => {
        const html = document.documentElement
        if (theme === "auto") {
            const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches
            html.setAttribute("data-bs-theme", prefersDark ? "dark" : "light")
        } else {
            html.setAttribute("data-bs-theme", theme)
        }
        localStorage.setItem("theme", theme)
    }, [theme])

    return (
        <div>
            <title>Settings</title>
            <Navbar user={user}></Navbar>
            <div className="text-center">
                <h1>Settings</h1>
                <h2>Theme</h2>
                <div className="d-flex gap-3 justify-content-center">
                    <button className="btn btn-primary" onClick={() => setTheme("auto")}>Auto</button>
                    <button className="btn btn-secondary" onClick={() => setTheme("light")}>Light mode</button>
                    <button className="btn btn-dark" onClick={() => setTheme("dark")}>Dark mode</button>
                </div>
            </div>
            
        </div>
    )
}

export default Settings