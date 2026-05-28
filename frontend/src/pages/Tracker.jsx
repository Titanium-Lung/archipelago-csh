import { useParams, Link } from "react-router-dom"
import { useEffect, useState } from "react"

function Tracker() {
    const { slot } = useParams()
    const [items, setItems] = useState({})

    useEffect(() => {
        async function fetchItems() {
            const response = await fetch(`http://localhost:5001/tracker/${slot}`, {
                method: "GET"
            })

            const result = await response.json()

            if (response.ok) {
                console.log("Successfully fetched items")
                setItems(result.items)
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
            <Link to="/multitracker">Back to Multiworld Tracker</Link>
        </div>
    )
}

export default Tracker