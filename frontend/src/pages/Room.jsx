import { useEffect, useState, useRef } from "react"
import { useNavigate, Link } from "react-router-dom"
import logo from "../assets/CSH Archipelago Logo.svg"

function Room() {
    const navigate = useNavigate()
    const bottomRef = useRef(null)

    const [port, setPort] = useState("")
    const [log, setLog] = useState(["Populating log..."])
    const [players, setPlayers] = useState([])

    useEffect(() => {
        async function restartServer() {
            const response = await fetch("http://localhost:5001/restart", {
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

    useEffect(() => {
        async function fetchPlayers() {
            const response = await fetch("http://localhost:5001/players", {
                method: "GET"
            })

            const result = await response.json()

            if (response.ok) {
                setPlayers(result.players)
            }
        }
        fetchPlayers()
    }, [])

    useEffect(() => {
        if (bottomRef.current) {
            bottomRef.current.scrollTop = bottomRef.current.scrollHeight
        }
    }, [log])

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

    async function sendServerCommand(command) {
        const response = await fetch("http://localhost:5001/command", {
            method: "POST",
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: command })
        })

        const result = await response.json()

        if (!response.ok) {
            console.log("Failed to send command to server")
        }
    }

    function sendToPage(url) {
        navigate(url)
    }

    return (
        <div>
            <nav className="navbar navbar-expand-lg navbar-dark navbar-sticky bg-primary px-3 px-md-5 mb-4">
                <a className="navbar-brand" href="/">
                    <img src={logo} style={{ height: "40px", width: "auto" }} /> Archipelago Host
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
                            <img src="https://profiles.csh.rit.edu/image/test"/>
                            Testing Tester
                            <span className="caret"></span>
                            </a>
                            <div className="dropdown-menu" aria-labelledby="user01">
                                <a className="dropdown-item" href="#">Profile</a>
                                <a className="dropdown-item" href="#">Settings</a>
                                <div className="dropdown-divider"></div>
                                <a className="dropdown-item" href="#">Logout</a>
                            </div>
                        </li>
                    </ul>
                </div>
            </nav>
            <div style={{textAlign: 'center'}}>
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
                <div style={{padding: '10px'}}>
                    <button className="btn btn-primary" onClick={() => sendToPage("/multitracker")}>Multiworld Tracker</button>
                </div>
                <div style={{paddingBottom: '20px'}}>
                    <button className="btn btn-primary" onClick={() => sendToPage("/spheres")}>Sphere Tracker</button>
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
                                {players.map(player => (
                                    <tr>
                                        <td>{player.slot}</td>
                                        <td>{player.name}</td>
                                        <td>{player.game}</td>
                                        {
                                            'patch' in player ? (
                                                <td><a href={`http://localhost:5001/players/${player.patch}`}>Download patch file</a></td>
                                            ) : (
                                                <td>No patch file to download</td>
                                            )
                                        }
                                        <td><Link to={`/tracker/${player.slot}`}>Tracker</Link></td>
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
                <div>
                    <input type="text" id="input" name="Server command" placeholder="Server command" onKeyUp={handleKeyUp} style={{width: '500px', marginBottom: '10px', marginRight: '20px'}} />
                    <Link to="/log">Full log</Link>
                </div>
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