import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { useUser } from "../UserContext"
import logo from "../assets/CSH Archipelago Logo.svg"

function Multitracker() {
    const user = useUser()

    const [players, setPlayers] = useState([])
    const [totals, setTotals] = useState({})
    const [hints, setHints] = useState([])

    const [gamesSortedColumn, setGamesSortedColumn] = useState(localStorage.getItem("gamesSortedColumn") || null)
    const [gamesSortDirection, setGamesSortDirection] = useState(localStorage.getItem("gamesSortDirection") || null)
    const [hintsSortedColumn, setHintsSortedColumn] = useState(localStorage.getItem("hintsSortedColumn") || null)
    const [hintsSortDirection, setHintsSortDirection] = useState(localStorage.getItem("hintsSortDirection") || null)

    const [filteredPlayers, setFilteredPlayers] = useState([])
    const [filterGames, setFilterGames] = useState('')
    const [filteredHints, setFilteredHints] = useState([])
    const [filterHints, setFilterHints] = useState('')

    useEffect(() => {
        async function fetchMultiworld() {
            const response = await fetch("http://localhost:5001/tracker", {
                method: "GET"
            })

            const result = await response.json()

            if (response.ok) {
                console.log("Successfully fetched players")
                setPlayers(result.players)
                setFilteredPlayers(result.players)
                setTotals(result.totals)
                setHints(result.hints)
                setFilteredHints(result.hints)
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

    useEffect(() => {
        const filteredGames = []

        players.forEach((player) => {
            if (player["name"].toLowerCase().includes(filterGames.toLowerCase()) ||
                    player["game"].toLowerCase().includes(filterGames.toLowerCase()) ||
                    String(player["slot"]).includes(filterGames.toLowerCase())) {
                filteredGames.push(player)
            }
        })

        setFilteredPlayers(filteredGames)
    }, [filterGames])

    useEffect(() => {
        const filteredItems = []

        hints.forEach((hint) => {
            if (hint["finding_player"].toLowerCase().includes(filterHints.toLowerCase()) ||
                    hint["receiving_player"].toLowerCase().includes(filterHints.toLowerCase()) ||
                    hint["item"].toLowerCase().includes(filterHints.toLowerCase()) ||
                    hint["location"].toLowerCase().includes(filterHints.toLowerCase()) ||
                    hint["game"].toLowerCase().includes(filterHints.toLowerCase()) ||
                    hint["entrance"].toLowerCase().includes(filterHints.toLowerCase())) {
                filteredItems.push(hint)
            }
        })

        setFilteredHints(filteredItems)
    }, [filterHints])

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

    const sortedPlayers = gamesSortedColumn ? [...filteredPlayers].sort((a, b) => {
        if (a[gamesSortedColumn] < b[gamesSortedColumn]) return gamesSortDirection === "asc" ? -1 : 1
        if (a[gamesSortedColumn] > b[gamesSortedColumn]) return gamesSortDirection === "asc" ? 1 : -1
        return 0
    }) : filteredPlayers

    const sortedHints = hintsSortedColumn ? [...filteredHints].sort((a, b) => {
        if (a[hintsSortedColumn] < b[hintsSortedColumn]) return hintsSortDirection === "asc" ? -1 : 1
        if (a[hintsSortedColumn] > b[hintsSortedColumn]) return hintsSortDirection === "asc" ? 1 : -1
        return 0
    }) : filteredHints

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
                            <img src={`https://profiles.csh.rit.edu/image/${user?.username}`} style={{ height: "40px", width: "auto", padding: "5px"}} className="rounded-circle"/>
                            {user?.username}
                            <span className="caret"></span>
                            </a>
                            <div className="dropdown-menu" aria-labelledby="user01">
                                <a className="dropdown-item" href={`https://profiles.csh.rit.edu/user/${user?.username}`}>Profile</a>
                                <div className="dropdown-divider"></div>
                                <a className="dropdown-item" href="http://localhost:5001/logout">Logout</a>
                            </div>
                        </li>
                    </ul>
                </div>
            </nav>
            <h1 style={{textAlign: 'center'}}>Multiworld Tracker</h1>
            <div className="mx-md-5 m-3">
                <input type="text" id="input" name="search" placeholder="Search" value={filterGames} onChange={e => setFilterGames(e.target.value)} />
            </div>
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
            <div className="mx-md-5 m-3">
                <input type="text" id="input" name="search" placeholder="Search" value={filterHints} onChange={e => setFilterHints(e.target.value)} />
            </div>
            {
                hints.length > 0 ? (
                    <div className="d-flex justify-content-center mx-md-5 mb-4 table-contained">
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
                                                    true: "✔",
                                                    false: "",
                                                }[hint.found] ?? "?"
                                            }
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="d-flex mx-md-5">
                        <p>No hints</p>
                    </div>
                )
            }
        </div>
    )


}

export default Multitracker