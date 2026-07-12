import { useEffect, useState, useRef } from "react"
import { useNavigate, Link, useParams } from "react-router-dom"
import { useUser } from "../UserContext"
import { Navbar } from "../Navbar"

function Room() {
    const { roomId } = useParams()

    const navigate = useNavigate()
    const bottomRef = useRef(null)
    const [initialFetch, setInitialFetch] = useState(true)
    const user = useUser()

    const [port, setPort] = useState("")
    const [log, setLog] = useState(["Populating log..."])
    const [players, setPlayers] = useState([])
    const [admin, setAdmin] = useState('')

    useEffect(() => {
        async function restartServer() {
            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/restart/${roomId}`, {
                method: "PUT"
            })

            const result = await response.json()

            if (!response.ok) {
                console.log("An error occured")
            }
        }
        restartServer()
    }, [])

    useEffect(() => {
        async function fetchRoom() {
            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/room/${roomId}`, {
                method: "GET"
            })

            const result = await response.json()

            if (response.ok) {
                setPort(result.port)
                setAdmin(result.admin)
            } 
        }
        fetchRoom()
    }, [])

    useEffect(() => {
        async function fetchLog() {
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

        // Every 2 seconds, fetch the log 
        const interval = setInterval(fetchLog, 2000)
        return () => clearInterval(interval)
    }, [])

    useEffect(() => {
        async function fetchPlayers() {
            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/players/${roomId}`, {
                method: "GET"
            })

            const result = await response.json()

            if (response.ok) {
                setPlayers(result.players)
            }
        }
        fetchPlayers()
    }, [])

    // Autoscroll log at the begining after fetching the log
    useEffect(() => {
        if (!initialFetch && bottomRef.current) {
            bottomRef.current.scrollTop = bottomRef.current.scrollHeight
        }
    }, [initialFetch])

    // Autoscroll the log when it's updated 
    useEffect(() => {
        setTimeout(() => {
            const logBox = bottomRef.current
            if (!logBox) return

            const isAtBottom = logBox.scrollHeight - logBox.scrollTop <= logBox.clientHeight + 60
            
            if (isAtBottom) {
                logBox.scrollTop = logBox.scrollHeight
            }
        }, 0)
    }, [log])

    const handleKeyUp = async (event) => {
        if (event.key === 'Enter') {
            console.log(event.target.value)
            try {
                const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/command/${roomId}`, {
                    method: "POST",
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: event.target.value }),
                    credentials: "include"
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

    function sendToPage(url) {
        navigate(url)
    }

    return (
        <div>
            <title>{`Room ${port}`}</title>
            <Navbar user={user}></Navbar>
            <div className="text-center">
                <h1>Room</h1>
                <p>This server shuts down automatically after 2 hours. Reload this page to restart it.</p>
                {
                    port != "" ? (
                        <div>
                            <p className="d-flex gap-2 align-items-center justify-content-center">
                                Port: <strong>{port}</strong> 
                                <button className="btn btn-copy" onClick={() => {navigator.clipboard.writeText(port)}}>Copy</button>
                            </p>
                            <p className="d-flex gap-2 align-items-center justify-content-center">
                                Connect to: <strong>archipelago.csh.rit.edu:{port}</strong> 
                                <button className="btn btn-copy" onClick={() => {navigator.clipboard.writeText(`archipelago.csh.rit.edu:${port}`)}}>Copy</button>
                            </p>
                        </div>
                    ) : (
                        <div>
                            <p>No server currently running</p>
                        </div>
                    )
                }
                <div>
                    <Link to={`/multitracker/${roomId}`}>Multiworld Tracker</Link>
                </div>
                <div style={{paddingBottom: '20px'}}>
                    <Link to={`/spheres/${roomId}`}>Sphere Tracker</Link>
                </div>
            </div>
            {
                players.length > 0 ? (
                    <div className="d-flex justify-content-center mx-md-5">
                        <table className="table table-bordered">
                            <thead>
                                <tr className="table-primary">
                                    <th>Id</th>
                                    <th>Name</th>
                                    <th>Game</th>
                                    <th>Patch file</th>
                                    <th>Tracker</th>
                                </tr>
                            </thead>
                            <tbody>
                                {players.map((player, index) => (
                                    <tr key={index}>
                                        <td>{player.slot}</td>
                                        <td>{player.name}</td>
                                        <td>{player.game}</td>
                                        {
                                            'patch' in player ? (
                                                <td><a href={`${import.meta.env.VITE_BACKEND_URL}/players/${roomId}/${player.patch}`}>Download patch file</a></td>
                                            ) : (
                                                <td>No patch file to download</td>
                                            )
                                        }
                                        <td><Link to={`/tracker/${roomId}/${player.slot}`}>Tracker</Link></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div>
                        <p>Populating players</p>
                    </div>
                )
            }
            <div className="mx-md-5">
                {
                    admin === user?.uuid ? (
                        <div>
                            <input type="text" id="input" name="Server command" placeholder="Server command" onKeyUp={handleKeyUp} style={{width: '500px', marginBottom: '10px', marginRight: '20px'}} />
                            <Link to={`/log/${roomId}`}>Full log</Link>
                        </div>
                    ) : (
                        <Link to={`/log/${roomId}`}>Full log</Link>
                    )
                }
                <div style={{marginBottom: '20px', height: '500px', overflowY: 'scroll'}} ref={bottomRef}>
                    {log.map((line, index) => (
                        <p style={{margin: '0'}} key={index}>{line}</p>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default Room