import { useParams, Link, useNavigate } from "react-router-dom"
import { useEffect, useState } from "react"
import logo from "../assets/CSH Archipelago Logo.svg"

function Tracker() {
    const navigate = useNavigate()
    const { slot } = useParams()
    const [items, setItems] = useState([])
    const [hints, setHints] = useState([])
    const [locations, setLocations] = useState([])

    const [itemsSortedColumn, setItemsSortedColumn] = useState(localStorage.getItem("itemsSortedColumn") || null)
    const [itemsSortDirection, setItemsSortDirection] = useState(localStorage.getItem("itemsSortDirection") || null)
    const [locationsSortedColumn, setLocationsSortedColumn] = useState(localStorage.getItem("locationsSortedColumn") || null)
    const [locationsSortDirection, setLocationsSortDirection] = useState(localStorage.getItem("locationsSortDirection") || null)
    const [hintsSortedColumn, setHintsSortedColumn] = useState(localStorage.getItem("hintsSortedColumn") || null)
    const [hintsSortDirection, setHintsSortDirection] = useState(localStorage.getItem("hintsSortDirection") || null)

    useEffect(() => {
        async function fetchItems() {
            const response = await fetch(`http://localhost:5001/tracker/${slot}`, {
                method: "GET"
            })

            const result = await response.json()

            if (response.ok) {
                console.log("Successfully fetched items")
                const itemDict = result.items
                const itemList = []
                
                Object.keys(itemDict).forEach((itemKey) => {
                    const item = {}
                    item["name"] = itemKey
                    item["count"] = itemDict[itemKey]["count"]
                    item["last_order_received"] = itemDict[itemKey]["last_order_received"]

                    itemList.push(item)
                })
                
                setItems(itemList)

                setHints(result.hints)
                setLocations(result.locations)
            }
        }
        fetchItems()
    }, [])

    useEffect(() => {
        if (itemsSortedColumn) {
            localStorage.setItem("itemsSortedColumn", itemsSortedColumn)
        }
    }, [itemsSortedColumn])

    useEffect(() => {
        if (itemsSortDirection) {
            localStorage.setItem("itemsSortDirection", itemsSortDirection)
        }
    }, [itemsSortDirection])

    useEffect(() => {
        if (locationsSortedColumn) {
            localStorage.setItem("locationsSortedColumn", locationsSortedColumn)
        }
    }, [locationsSortedColumn])

    useEffect(() => {
        if (locationsSortDirection) {
            localStorage.setItem("locationsSortDirection", locationsSortDirection)
        }
    }, [locationsSortDirection])

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

    function sendToMultiTracker() {
        navigate("/multitracker")
    }

    function setItemSort(column) {
        if (itemsSortedColumn === column) {
            setItemsSortDirection(itemsSortDirection === "asc" ? "desc" : "asc")
        } else {
            setItemsSortedColumn(column)
            setItemsSortDirection("asc")
        }
    }

    function setLocationSort(column) {
        if (locationsSortedColumn === column) {
            setLocationsSortDirection(locationsSortDirection === "asc" ? "desc" : "asc")
        } else {
            setLocationsSortedColumn(column)
            setLocationsSortDirection("asc")
        }
    }

    function setHintSort(column) {
        if (hintsSortedColumn === column) {
            setHintsSortDirection(hintsSortDirection === "asc" ? "desc" : "asc")
        } else {
            setHintsSortedColumn(column)
            setHintsSortDirection("asc")
        }
    }

    const sortedItems = itemsSortedColumn ? [...items].sort((a, b) => {
        if (a[itemsSortedColumn] < b[itemsSortedColumn]) return itemsSortDirection === "asc" ? -1 : 1
        if (a[itemsSortedColumn] > b[itemsSortedColumn]) return itemsSortDirection === "asc" ? 1 : -1
        return 0
    }) : items

    const sortedLocations = locationsSortedColumn ? [...locations].sort((a, b) => {
        if (a[locationsSortedColumn] < b[locationsSortedColumn]) return locationsSortDirection === "asc" ? -1 : 1
        if (a[locationsSortedColumn] > b[locationsSortedColumn]) return locationsSortDirection === "asc" ? 1 : -1
        return 0
    }) : locations

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
            <h1 style={{textAlign: 'center'}}>Individual Tracker</h1>
            <div className="d-flex justify-content-center mx-md-5">
                <table className="table table-bordered table-hover">
                    <thead>
                        <tr className="table table-primary">
                            <th onClick={() => setItemSort("name")} style={{cursor: 'pointer'}}>Item</th>
                            <th onClick={() => setItemSort("count")} style={{cursor: 'pointer'}}>Count</th>
                            <th onClick={() => setItemSort("last_order_received")} style={{cursor: 'pointer'}}>Last Order Received</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedItems.map(item => (
                            <tr>
                                <td>{item.name}</td>
                                <td>{item.count}</td>
                                <td>{item.last_order_received}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <h2 style={{textAlign: 'center'}}>Location checks</h2>
            {
                locations.length > 0 ? (
                    <div className="d-flex justify-content-center mx-md-5">
                        <table className="table table-bordered table-hover">
                            <thead>
                                <tr className="table table-primary">
                                    <th onClick={() => setLocationSort("name")} style={{cursor: 'pointer'}}>Location</th>
                                    <th onClick={() => setLocationSort("checked")} style={{cursor: 'pointer'}}>Checked</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sortedLocations.map(location => (
                                    <tr>
                                        <td>{location.name}</td>
                                        <td>
                                            {
                                                {
                                                    true: "Yes",
                                                    false: "No",
                                                }[location.checked] ?? "?"
                                            }
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div>
                        <p>Populating location info...</p>
                    </div>
                )
            }
            <h2 style={{textAlign: 'center'}}>Hints</h2>
            <div className="d-flex justify-content-center mx-md-5">
                <table className="table table-bordered table-hover">
                    <thead>
                        <tr className="table table-primary">
                            <th onClick={() => setHintSort("finding_player")} style={{cursor: 'pointer'}}>Finder</th>
                            <th onClick={() => setHintSort("receiving_player")} style={{cursor: 'pointer'}}>Receiver</th>
                            <th onClick={() => setHintSort("item")} style={{cursor: 'pointer'}}>Item</th>
                            <th onClick={() => setHintSort("location")} style={{cursor: 'pointer'}}>Location</th>
                            <th onClick={() => setHintSort("game")} style={{cursor: 'pointer'}}>Game</th>
                            <th onClick={() => setHintSort("entrance")} style={{cursor: 'pointer'}}>Entrance</th>
                            <th onClick={() => setHintSort("found")} style={{cursor: 'pointer'}}>Found</th>
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
            <div style={{textAlign: 'center', paddingBottom: '20px'}}>
                <button className="btn btn-primary" onClick={sendToMultiTracker}>Back to Multiworld Tracker</button>
            </div>
        </div>
    )
}

export default Tracker