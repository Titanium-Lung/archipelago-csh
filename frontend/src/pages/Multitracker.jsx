import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import logo from "../assets/CSH Archipelago Logo.svg"

function Multitracker() {
    const [players, setPlayers] = useState([])
    const [totals, setTotals] = useState({})
    const [hints, setHints] = useState([])

    const [gamesSortedColumn, setGamesSortedColumn] = useState(localStorage.getItem("gamesSortedColumn") || null)
    const [gamesSortDirection, setGamesSortDirection] = useState(localStorage.getItem("gamesSortDirection") || null)
    const [hintsSortedColumn, setHintsSortedColumn] = useState(localStorage.getItem("hintsSortedColumn") || null)
    const [hintsSortDirection, setHintsSortDirection] = useState(localStorage.getItem("hintsSortDirection") || null)

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

    useEffect(() => {
        if (gamesSortedColumn) {
            localStorage.setItem("gamesSortedColumn", gamesSortedColumn)
        }
    }, [gamesSortedColumn])

    useEffect(() => {
        if (gamesSortDirection) {
            localStorage.setItem("gamesSortDirection", gamesSortDirection)
        }
    }, [gamesSortDirection])
    useEffect(() => {
        if (hintsSortedColumn) {
            localStorage.setItem("hintsSortedColumn", hintsSortedColumn)
        }
    }, [hintsSortedColumn])

    useEffect(() => {
        if (hintsSortDirection) {
            localStorage.setItem("hintsSortDirection", hintsSortDirection)
        }
    }, [hintsSortDirection])

    function setSort(column, table) {
        if (table === "games") {
            if (gamesSortedColumn === column) {
                setGamesSortDirection(gamesSortDirection === "asc" ? "desc" : "asc")
            } else {
                setGamesSortedColumn(column)
                setGamesSortDirection("asc")
            }
        } else if (table === "hints") {
            if (hintsSortedColumn === column) {
                setHintsSortDirection(hintsSortDirection === "asc" ? "desc" : "asc")
            } else {
                setHintsSortedColumn(column)
                setHintsSortDirection("asc")
            }
        }
    }

    const sortedPlayers = gamesSortedColumn ? [...players].sort((a, b) => {
        if (a[gamesSortedColumn] < b[gamesSortedColumn]) return gamesSortDirection === "asc" ? -1 : 1
        if (a[gamesSortedColumn] > b[gamesSortedColumn]) return gamesSortDirection === "asc" ? 1 : -1
        return 0
    }) : players

    const sortedHints = hintsSortedColumn ? [...hints].sort((a, b) => {
        if (a[hintsSortedColumn] < b[hintsSortedColumn]) return hintsSortDirection === "asc" ? -1 : 1
        if (a[hintsSortedColumn] > b[hintsSortedColumn]) return hintsSortDirection === "asc" ? 1 : -1
        return 0
    }) : hints

    return (
        <div>
            <nav className="navbar navbar-expand-lg navbar-dark bg-primary px-3 px-md-5 mb-4">
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
            <h1 style={{textAlign: 'center'}}>Multiworld Tracker</h1>
            {
                players.length > 0 ? (
                    <div className="d-flex justify-content-center mx-md-5">
                        <table className="table table-bordered table-hover">
                            <thead>
                                <tr className="table-primary">
                                    <th onClick={() => setSort("slot", "games")} style={{cursor: 'pointer'}}>Id</th>
                                    <th onClick={() => setSort("name", "games")} style={{cursor: 'pointer'}}>Name</th>
                                    <th onClick={() => setSort("game", "games")} style={{cursor: 'pointer'}}>Game</th>
                                    <th onClick={() => setSort("status", "games")} style={{cursor: 'pointer'}}>Status</th>
                                    <th onClick={() => setSort("checks_found", "games")} style={{cursor: 'pointer'}}>Checks</th>
                                    <th onClick={() => setSort("percent_checked", "games")} style={{cursor: 'pointer'}}>%</th>
                                    <th onClick={() => setSort("last_activity_num", "games")} style={{cursor: 'pointer'}}>Last Check</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sortedPlayers.map(player => (
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
                                        <td>{player.percent_checked.toFixed(2)}</td>
                                        <td>{player.last_activity}</td>
                                    </tr>
                                ))}
                                <tr style={{fontWeight: 'bold'}}>
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
            <h2 style={{textAlign: 'center'}}>Hints</h2>
            {
                hints.length > 0 ? (
                    <div className="d-flex justify-content-center mx-md-5">
                        <table className="table table-bordered table-hover">
                            <thead>
                                <tr className="table-primary">
                                    <th onClick={() => setSort("finding_player", "hints")} style={{cursor: 'pointer'}}>Finder</th>
                                    <th onClick={() => setSort("receiving_player", "hints")} style={{cursor: 'pointer'}}>Receiver</th>
                                    <th onClick={() => setSort("item", "hints")} style={{cursor: 'pointer'}}>Item</th>
                                    <th onClick={() => setSort("location", "hints")} style={{cursor: 'pointer'}}>Location</th>
                                    <th onClick={() => setSort("game", "hints")} style={{cursor: 'pointer'}}>Game</th>
                                    <th onClick={() => setSort("entrance", "hints")} style={{cursor: 'pointer'}}>Entrance</th>
                                    <th onClick={() => setSort("found", "hints")} style={{cursor: 'pointer'}}>Found</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sortedHints.map(hint => (
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