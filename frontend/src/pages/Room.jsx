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

    const handleKeyUp = async (event) => {
        if (event.key === 'Enter') {
            console.log(event.target.value)
            try {
                const response = await fetch("http://localhost:5001/command", {
                    method: "POST",
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: event.target.value })
                })

                const result = await response.json()

                if (!response.ok) {
                    console.log("Failed to send command to server")
                }
            } catch (error) {
                console.error("Error: " + error)
            }

            document.getElementById('input').value = ''
        }
    }

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
            <div class="log">
                <input type="text" id="input" name="Server command" placeholder="Server command" onKeyUp={handleKeyUp} />
            </div>
            <div class="log">
                <Link to="/log">Full log</Link>
            </div>
            <div class="log">
                {log.map((line, index) => (
                    <p key={index}>{line}</p>
                ))}
            </div>
        </div>
    )
}

export default Room