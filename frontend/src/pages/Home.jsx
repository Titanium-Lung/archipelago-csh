import { useEffect, useState } from "react"
import { useNavigate, Link } from "react-router-dom"
import { useUser } from "../UserContext"
import { Navbar } from "../Navbar"

function Home() {
    const navigate = useNavigate()
    const user = useUser()

    const [deletingRoomId, setDeletingRoomId] = useState(null)

    const [rooms, setRooms] = useState([])
    const [file, setFile] = useState(null) 
    const [message, setMessage] = useState("")
    const [port, setPort] = useState("")
    const [roomId, setRoomId] = useState("")

    useEffect(() => {
        async function fetchRooms() {
            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/rooms`, {
                method: "PUT",
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ data: Intl.DateTimeFormat().resolvedOptions()})
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

        setDeletingRoomId(null) // Because of confirm delete dialog box
    }

    function sendToRoom() {
        navigate(`/room/${roomId}`)
    }

    return (
        <div>
            <Navbar user={user}></Navbar>
            <div className="text-center">
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
                                        <th>Name</th>
                                        <th>Port</th>
                                        <th>Room Page</th>
                                        <th>Multitracker</th>
                                        <th>Start</th>
                                        <th>Running?</th>
                                        <th>Delete</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {rooms.map((room, index) => (
                                        <tr key={index}>
                                            <td>{room.name}</td>
                                            <td>{room.port}</td>
                                            <td><Link to={`/room/${room.room_id}`}>Room</Link></td>
                                            <td><Link to={`/multitracker/${room.room_id}`}>Tracker</Link></td>
                                            <td>{room.start}</td>
                                            <td>
                                                {
                                                    {
                                                        true: "✔",
                                                        false: "✖",
                                                    }[room.running] ?? "?"
                                                }
                                            </td>
                                            <td>
                                                {
                                                    user?.uuid === room.admin_uuid ? (
                                                        <div>
                                                            <button className="btn btn-danger" onClick={() => setDeletingRoomId(room.room_id)}>Delete</button>
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

                            {deletingRoomId && (
                                <div className="modal show d-block" tabIndex="-1">
                                    <div className="modal-dialog">
                                        <div className="modal-content">
                                            <div className="modal-header">
                                                <h5 className="modal-title">Are you sure you want to delete this room?</h5>
                                                <button className="btn-close" onClick={() => setDeletingRoomId(null)} />
                                            </div>
                                            <div className="modal-body">
                                                <p>This action cannot be undone.</p>
                                            </div>
                                            <div className="modal-footer">
                                                <button className="btn btn-secondary" onClick={() => setDeletingRoomId(null)}>Cancel</button>
                                                <button className="btn btn-danger" onClick={() => deleteRoom(deletingRoomId)}>Confirm</button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {deletingRoomId && <div className="modal-backdrop show" />}
                        </div>
                    ) : ( 
                        <p>None</p>
                    )
                }
            </div>
        </div>
    )
}

export default Home
