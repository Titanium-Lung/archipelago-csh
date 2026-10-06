import { useEffect, useState, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom"
import { Virtuoso } from "react-virtuoso"

function Log() {
    const { roomId } = useParams()

    const bottomRef = useRef(null)
    const navigate = useNavigate()
    const [initialFetch, setInitialFetch] = useState(true)
    const [log, setLog] = useState(["Populating log..."])

    useEffect(() => {
        async function fetchInitialLog() {
            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/log/${roomId}`, {
                method: "GET"
            })

            const result = await response.json()

            if (response.ok) {
                setLog(result.lines)
                if (initialFetch) {
                    setInitialFetch(false)
                }
            }
        }

        fetchInitialLog()

        const eventSource = new EventSource(`${import.meta.env.VITE_BACKEND_URL}/log/stream/${roomId}`)

        eventSource.onmessage = (event) => {
            setLog(prev => [...prev, event.data])
        }

        eventSource.onerror = () => {
            eventSource.close()
        }

        return () => eventSource.close()
    }, [])

    function sendToPage(url) {
        navigate(url)
    }

    return (
        <div className="m-3">
            <button className="btn btn-primary" style={{marginBottom: '10px'}} onClick={() => sendToPage(`/room/${roomId}`)}>Back to room</button>
            <h2>Log</h2>
            <div style={{ height: '87.5vh' }}>
                <Virtuoso
                    data={log}
                    style={{ height: '100%' }}
                    ref={bottomRef}
                    itemContent={(_i, item) => <p style={{ margin: '0' }}>{item}</p>}
                    followOutput={(isAtBottom) => isAtBottom ? 'auto' : false}
                />
            </div>
        </div>
    )

}

export default Log
