import { useEffect, useState } from "react"
import { useUser } from "../UserContext"
import logo from "../assets/CSH Archipelago Logo.svg"

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
            <nav className="navbar navbar-expand-lg navbar-dark navbar-sticky bg-primary px-3 px-md-5 mb-4">
                <a className="navbar-brand" href="/">
                    <img src={logo} style={{ height: "40px", width: "auto" }} /> Archipelago
                </a>
                <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarColor01" aria-controls="navbarColor01" aria-expanded="false" aria-label="Toggle navigation">
                    <span className="navbar-toggler-icon"></span>
                </button>

                <div className="collapse navbar-collapse" id="navbarColor01">

                    <ul className="navbar-nav me-auto">
                        <li className="nav-item active">
                            <a className="nav-link" href="/">Home</a>
                        </li>
                        <li className="nav-item">
                            <a className="nav-link" href="https://github.com/Titanium-Lung/archipelago-csh">Github</a>
                        </li>
                    </ul>
                    <ul className="nav navbar-nav">
                        <li className="nav-item navbar-user dropdown">
                            <a className="nav-link dropdown-toggle" data-bs-toggle="dropdown" href="#" id="user01">
                            <img src={user?.picture_url} style={{ height: "40px", width: "auto", padding: "5px"}} className="rounded-circle"/>
                            {user?.username}
                            <span className="caret"></span>
                            </a>
                            <div className="dropdown-menu" aria-labelledby="user01">
                                <a className="dropdown-item" href="https://github.com/Titanium-Lung/archipelago-csh/issues">Report an issue</a>
                                <a className="dropdown-item" href={`https://profiles.csh.rit.edu/user/${user?.username}`}>Profile</a>
                                <div className="dropdown-divider"></div>
                                <a className="dropdown-item" href={`${import.meta.env.VITE_BACKEND_URL}/logout`}>Logout</a>
                            </div>
                        </li>
                    </ul>
                </div>
            </nav>
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