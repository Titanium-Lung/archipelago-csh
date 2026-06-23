import { useEffect, useState } from "react"
import { useNavigate, Link } from "react-router-dom"
import { useUser } from "../UserContext"
import logo from "../assets/CSH Archipelago Logo.svg"

function Home() {
    const navigate = useNavigate()
    const user = useUser()

    const [showModal, setShowModal] = useState(false)

    const [rooms, setRooms] = useState([])
    const [file, setFile] = useState(null) 
    const [message, setMessage] = useState("")
    const [port, setPort] = useState("")
    const [roomId, setRoomId] = useState("")

    useEffect(() => {
        async function fetchRooms() {
            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/rooms`, {
                method: "GET"
            })

            const result = await response.json()

            if (response.ok) {
                setRooms(result.rooms)
            } 
        }
        fetchRooms()
    }, [])

    // For file picker
    function handleFileChange(event) {
        setFile(event.target.files[0])
    }

    async function handleUpload() {
        if (!file) {
            setMessage("Please select a file first.")
            return
        }
        
        try {
            const formData = new FormData()
            formData.append("file", file)

            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/upload`, {
                method: "POST",
                body: formData,
                credentials: "include"
            })

            const result = await response.json()

            if (response.ok) {
                setMessage("Server started!")
                setPort(result.port)
                setRoomId(result.room_id)
            } else {
                setMessage("Error: " + result.error)
            }
        } catch (error) {
            setMessage("Error: " + error.message)
        }
    }

    async function deleteRoom(roomId) {
        const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/delete/${roomId}`, {
            method: "DELETE",
            credentials: "include"
        })

        const result = await response.json()

        if (response.ok) {
            console.log(result.message)
        } else {
            console.log(result.error)
        }
        window.location.reload()

        setShowModal(false) // Because of confirm delete dialog box
    }

    function sendToRoom() {
        navigate(`/room/${roomId}`)
    }

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
            <div style={{textAlign: 'center'}}>
                <h1>Archipelago Host</h1>
                {
                    // Only CSH accounts can upload files 
                    user?.csh ? (
                        <div className="form-group">
                            <input type="file" accept=".zip" onChange={handleFileChange} className="form-control-file" id="exampleInputFile" aria-describedby="fileHelp" />
                            <button className="btn btn-primary" onClick={handleUpload}>Upload</button>
                            <br></br>
                            <small id="fileHelp" className="form-text text-muted">Upload the zip file of your generated multiworld</small>
                        </div>
                    ) : (<div></div>)
                }
                <p>{message}</p>
                {
                    port != "" && (
                    <div>
                        <p>Port: {port}</p> 
                        <button className="btn btn-success" onClick={sendToRoom}>Go to room</button>
                    </div>
                    )
                }
                <h2>Current Rooms</h2>
                {
                    rooms.length > 0 ? (
                        <div className="d-flex justify-content-center mx-md-5">
                            <table className="table table-bordered">
                                <thead>
                                    <tr className="table-primary">
                                        <th>Port</th>
                                        <th>Room Page</th>
                                        <th>Multitracker</th>
                                        <th>Start</th>
                                        <th>Delete</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {rooms.map((room, index) => (
                                        <tr key={index}>
                                            <td>{room.port}</td>
                                            <td><Link to={`http://localhost:5173/room/${room.room_id}`}>Room</Link></td>
                                            <td><Link to={`http://localhost:5173/multitracker/${room.room_id}`}>Tracker</Link></td>
                                            <td>{room.start}</td>
                                            <td>
                                                {
                                                    user?.uuid === room.admin_uuid ? (
                                                        <div>
                                                            <button className="btn btn-danger" onClick={() => setShowModal(true)}>Delete</button>
                                                            
                                                            {showModal && (
                                                                <div className="modal show d-block" tabIndex="-1">
                                                                    <div className="modal-dialog">
                                                                        <div className="modal-content">
                                                                            <div className="modal-header">
                                                                                <h5 className="modal-title">Are you sure you want to delete this room?</h5>
                                                                                <button className="btn-close" onClick={() => setShowModal(false)} />
                                                                            </div>
                                                                            <div className="modal-body">
                                                                                <p>This action cannot be undone.</p>
                                                                            </div>
                                                                            <div className="modal-footer">
                                                                                <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                                                                                <button className="btn btn-danger" onClick={() => deleteRoom(room.room_id)}>Confirm</button>
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            )}

                                                            {showModal && <div className="modal-backdrop show" />}
                                                        </div>
                                                    ) : (
                                                        <p>You can't delete this room</p>
                                                    )
                                                }
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : ( 
                        <p>None</p>
                    )
                }
                

                {showModal && <div className="modal-backdrop show" />}
            </div>
        </div>
    )
}

export default Home
