import { useEffect, useState } from "react"
import { Link } from "react-router-dom"

function Room() {
    const [port, setPort] = useState("")
    const [log, setLog] = useState(["Populating log..."])

    useEffect(() => {
        async function fetchPort() {
            const response = await fetch("http://localhost:5001/room", {
                method: "GET"
            })

            const result = await response.json()

            if (response.ok) {
                setPort(result.port)
            } 
        }
        fetchPort()
    }, [])

    useEffect(() => {
        async function fetchLog() {
            const response = await fetch("http://localhost:5001/log/last", {
                method: "GET"
            })

            const result = await response.json()

            if (response.ok) {
                setLog(result.lines)
            }
        }

        const interval = setInterval(fetchLog, 2000)
        return () => clearInterval(interval)
    }, [])

    return (
        <div>
            <h1>Room</h1>
            {
                port != "" ? (
                    <div>
                        <p>Port: {port}</p>
                    </div>
                ) : (
                    <div>
                        <p>No server currently running</p>
                    </div>
                )
            }
            <Link to="/log">Full log</Link>
            <div class="log">
                {log.map((line, index) => (
                    <p key={index}>{line}</p>
                ))}
            </div>
        </div>
    )
}

export default Room