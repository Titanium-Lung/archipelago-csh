import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom"

function Log() {
    const { roomId } = useParams()

    const navigate = useNavigate()
    const [log, setLog] = useState(["Populating log..."])

    useEffect(() => {
        async function fetchLog() {
            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/log/${roomId}`, {
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

    function sendToPage(url) {
        navigate(url)
    }

    return (
        <div className="m-3">
            <button className="btn btn-primary" style={{marginBottom: '10px'}} onClick={() => sendToPage(`/room/${roomId}`)}>Back to room</button>
            <h2>Log</h2>
            <div>
                {log.map((line, index) => (
                    <p style={{margin: '0'}} key={index}>{line}</p>
                ))}
            </div>
        </div>
    )

}

export default Log