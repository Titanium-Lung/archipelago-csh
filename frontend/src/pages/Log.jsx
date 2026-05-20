import { useEffect, useState } from "react";
import { Link } from "react-router-dom"

function Log() {
    const [log, setLog] = useState(["Populating log..."])

    useEffect(() => {
        async function fetchLog() {
            const response = await fetch("http://localhost:5001/log", {
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
        <div class="log">
            <Link to="/room">Back to room</Link>
            <h2>Log</h2>
                <div>
                    {log.map((line, index) => (
                        <p key={index}>{line}</p>
                    ))}
                </div>
        </div>
    )

}

export default Log