import { useEffect, useState } from "react"

function Multitracker() {
    const [players, setPlayers] = useState([])
    const [totals, setTotals] = useState({})

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
                                        <td>{player.slot}</td>
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
        </div>
    )


}

export default Multitracker