import { useEffect, useState } from "react"
import { useUser } from "../UserContext"
import { Navbar } from "../Navbar"

function Settings() {
    const user = useUser()
    
    const [theme, setTheme] = useState(localStorage.getItem("theme") || "auto")
    const [slots, setSlots] = useState([])

    useEffect(() => {
        async function fetchSlots() {
            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/history`, {
                method: "GET",
                credentials: "include"
            })

            const result = await response.json()

            if (response.ok) {
                setSlots(result.slots)
            }
        }

        fetchSlots()
    }, [])

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
            <div className="text-center mb-3">
                <h1>Settings</h1>
                <h2>Theme</h2>
                <div className="d-flex gap-3 justify-content-center">
                    <button className="btn btn-primary" onClick={() => setTheme("auto")}>Auto</button>
                    <button className="btn btn-secondary" onClick={() => setTheme("light")}>Light mode</button>
                    <button className="btn btn-dark" onClick={() => setTheme("dark")}>Dark mode</button>
                </div>
            </div>
            <div className="d-flex justify-content-center mx-md-5">
                <table className="table table-bordered table-hover">
                    <thead>
                        <tr className="table table-primary">
                            <th>Name</th>
                            <th>Game</th>
                            <th>Checks</th>
                        </tr>
                    </thead>
                    <tbody>
                        {slots.map((slot, index) => (
                            <tr key={index}>
                                <td>{slot.name}</td>
                                <td>{slot.game}</td>
                                <td>{slot.checks}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

export default Settings