import { useEffect, useState } from "react"
import { Link } from "react-router-dom"

function Multitracker() {
    const [players, setPlayers] = useState([])
    const [totals, setTotals] = useState({})
    const [hints, setHints] = useState([])

    useEffect(() => {
        async function fetchMultiworld() {
            const response = await fetch("http://localhost:5001/tracker", {
                method: "GET"
            })

            const result = await response.json()

            if (response.ok) {
                console.log("Successfully fetched")
                setPlayers(result.players)
                setTotals(result.totals)
                setHints(result.hints)
            }
        }
        fetchMultiworld()
    }, [])


    return (
        <div>
            <h1>Multiworld Tracker</h1>
            {
                players.length > 0 ? (
                    <div>
                        <table>
                            <thead>
                                <tr>
                                    <th>Id</th>
                                    <th>Name</th>
                                    <th>Game</th>
                                    <th>Status</th>
                                    <th>Checks</th>
                                    <th>%</th>
                                    <th>Last Check</th>
                                </tr>
                            </thead>
                            <tbody>
                                {players.map(player => (
                                    <tr>
                                        <td><Link to={`/tracker/${player.slot}`}>{player.slot}</Link></td>
                                        <td>{player.name}</td>
                                        <td>{player.game}</td>
                                        <td>
                                            {
                                                {
                                                    0: "Disconnected",
                                                    5: "Connected",
                                                    10: "Ready",
                                                    20: "Playing",
                                                    30: "Goal Completed"
                                                }[player.status] ?? "Unknown Status"
                                            }
                                        </td>
                                        <td>{player.checks_found + "/" + player.total_checks}</td>
                                        <td>{(player.checks_found/player.total_checks).toFixed(2)}</td>
                                        <td>{player.last_activity}</td>
                                    </tr>
                                ))}
                                <tr>
                                    <td></td>
                                    <td>Totals</td>
                                    <td>All Games</td>
                                    <td>{totals.games_complete + "/" + totals.num_players + " Complete"}</td>
                                    <td>{totals.total_checked + "/" + totals.total_checks}</td>
                                    <td>{(totals.total_checked/totals.total_checks).toFixed(2)}</td>
                                    <td>{totals.recent_activity}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div>
                        <p>Populating players</p>
                    </div>
                )
            }
            <h2>Hints</h2>
            {
                hints.length > 0 ? (
                    <div>
                        <table>
                            <thead>
                                <tr>
                                    <th>Finder</th>
                                    <th>Receiver</th>
                                    <th>Item</th>
                                    <th>Location</th>
                                    <th>Game</th>
                                    <th>Entrance</th>
                                    <th>Found</th>
                                </tr>
                            </thead>
                            <tbody>
                                {hints.map(hint => (
                                    <tr>
                                        <td>{hint.finding_player}</td>
                                        <td>{hint.receiving_player}</td>
                                        <td>{hint.item}</td>
                                        <td>{hint.location}</td>
                                        <td>{hint.game}</td>
                                        <td>{hint.entrance}</td>
                                        <td>
                                            {
                                                {
                                                    true: "Yes",
                                                    false: "No",
                                                }[hint.found] ?? "?"
                                            }
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div>
                        <p>Populating hints</p>
                    </div>
                )
            }
        </div>
    )


}

export default Multitracker