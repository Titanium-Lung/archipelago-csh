import { useEffect, useState } from "react"
import { Navbar } from "../Navbar"
import { useUser } from "../UserContext"

function Stats() {
    const user = useUser()

    const [slots, setSlots] = useState([])
    const [totals, setTotals] = useState({})
    const [sessionTotals, setSessionTotals] = useState([])

    const [deletingRoomId, setDeletingRoomId] = useState(null)
    const [deletingSlot, setDeletingSlot] = useState(null)

    useEffect(() => {
        async function fetchStats() {
            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/stats`, {
                method: "GET",
                credentials: "include"
            })

            const result = await response.json()

            if (response.ok) {
                setSlots(result.slots)
                setTotals(result.totals)
                setSessionTotals(result.session_totals)
            } else {
                console.log(result.error)
            }
        }

        fetchStats()
    }, [])

    async function deleteSlot(roomId, slot) {
        const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/assign/${roomId}/${slot}`, {
            method: "DELETE",
            credentials: "include"
        })

        const result = await response.json()

        if (!response.ok) {
            console.log(result.error)
        }
        window.location.reload()

        setDeleting(null, null)
    }

    function setDeleting(room, slot) {
        setDeletingRoomId(room)
        setDeletingSlot(slot)
    }

    return (
        <div>
            <title>Stats</title>
            <Navbar user={user} />
            <div className="text-center">
                <h1>Stats</h1>
                <h2>Previous games</h2>
                <div className="d-flex justify-content-center mx-md-5">
                    <table className="table table-bordered table-hover">
                        <thead>
                            <tr className="table table-primary">
                                <th>Name</th>
                                <th>Game</th>
                                <th>Checks</th>
                                <th>Session Name</th>
                                <th>Remove</th>
                            </tr>
                        </thead>
                        <tbody>
                            {slots.map((slot, index) => (
                                <tr key={index}>
                                    <td>{slot.name}</td>
                                    <td>{slot.game}</td>
                                    <td>{slot.checks}</td>
                                    <td>{slot.room_name}</td>
                                    <td><button className="btn btn-danger" onClick={() => setDeleting(slot.room_id, slot.slot)}>Remove</button></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>

                    {deletingRoomId && (
                        <div className="modal show d-block" tabIndex="-1">
                            <div className="modal-dialog">
                                <div className="modal-content">
                                    <div className="modal-header">
                                        <h5 className="modal-title">Are you sure you want to remove this slot?</h5>
                                        <button className="btn-close" onClick={() => setDeleting(null, null)} />
                                    </div>
                                    <div className="modal-body">
                                        <p>If this archipelago session has been deleted, this action is permanent.</p>
                                    </div>
                                    <div className="modal-footer">
                                        <button className="btn btn-secondary" onClick={() => setDeleting(null, null)}>Cancel</button>
                                        <button className="btn btn-danger" onClick={() => deleteSlot(deletingRoomId, deletingSlot)}>Confirm</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {deletingRoomId && <div className="modal-backdrop show" />}
                </div>
                <div>
                    <h2>Overall stats</h2>
                    <div className="d-flex justify-content-center mx-md-5">
                        <table className="table table-bordered table-hover">
                            <thead>
                                <tr className="table table-primary">
                                    <th>Total Sessions</th>
                                    <th>Total Games</th>
                                    <th>Total Checks</th>
                                    <th>Average Games</th>
                                    <th>Average Checks Per Session</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>{totals.sessions}</td>
                                    <td>{totals.games}</td>
                                    <td>{totals.checks}</td>
                                    <td>{parseFloat(totals.average_games)}</td>
                                    <td>{parseFloat(totals.average_checks)}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                <div>
                    <h2>Stats by session</h2>
                    <div className="d-flex justify-content-center mx-md-5">
                        <table className="table table-bordered table-hover">
                            <thead>
                                <tr className="table table-primary">
                                    <th>Games</th>
                                    <th>Checks</th>
                                    <th>Average Checks</th>
                                    <th>Session Name</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sessionTotals.map((session, index) => (
                                    <tr key={index}>
                                        <td>{session.games}</td>
                                        <td>{session.checks}</td>
                                        <td>{parseFloat(session.average_checks)}</td>
                                        <td>{session.name}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Stats