import { useParams, Link } from "react-router-dom"
import { useEffect, useState } from "react"

function Tracker() {
    const { slot } = useParams()
    const [items, setItems] = useState({})
    const [hints, setHints] = useState([])
    const [locations, setLocations] = useState([])

    useEffect(() => {
        async function fetchItems() {
            const response = await fetch(`http://localhost:5001/tracker/${slot}`, {
                method: "GET"
            })

            const result = await response.json()

            if (response.ok) {
                console.log("Successfully fetched items")
                setItems(result.items)
                setHints(result.hints)
                setLocations(result.locations)
            }
        }
        fetchItems()
    }, [])

    return (
        <div>
            <h1>Individual Tracker</h1>
            <div>
                <table>
                    <thead>
                        <tr>
                            <th>Item</th>
                            <th>Count</th>
                            <th>Last Order Received</th>
                        </tr>
                    </thead>
                    <tbody>
                        {Object.keys(items).map(item => (
                            <tr>
                                <td>{item}</td>
                                <td>{items[item].count}</td>
                                <td>{items[item].last_order_received}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <h2>Location checks</h2>
            {
                locations.length > 0 ? (
                    <div>
                        <table>
                            <thead>
                                <tr>
                                    <th>Location</th>
                                    <th>Checked</th>
                                </tr>
                            </thead>
                            <tbody>
                                {locations.map(location => (
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
            <h2>Hints</h2>
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
            <Link to="/multitracker">Back to Multiworld Tracker</Link>
        </div>
    )
}

export default Tracker