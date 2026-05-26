import { useEffect, useState } from "react"

function Sphere() {
    const [sphereData, setSphereData] = useState([])

    useEffect(() => {
        async function fetchSpheres() {
            const response = await fetch("http://localhost:5001/spheres", {
                method: "GET"
            })

            const result = await response.json()

            if (response.ok) {
                console.log("Successfully fetched")
                setSphereData(result.items)
            }
        }
        fetchSpheres()
    }, [])

    return (
        <div>
            <h1>Sphere tracker</h1>
            <p>This tracker lists already found locations by their logical access sphere. 
                It ignores items that cannot be sent and will therefore differ from the sphere numbers in the spoiler playthrough.
                This tracker will automatically update itself periodically.</p>
            {
                sphereData.length > 0 ? (
                    <div>
                        <table>
                            <thead>
                                <tr>
                                    <th>Sphere</th>
                                    <th>Finder</th>
                                    <th>Receiver</th>
                                    <th>Item</th>
                                    <th>Location</th>
                                    <th>Game</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sphereData.map(item => (
                                    <tr>
                                        <td>{item.sphere}</td>
                                        <td>{item.from}</td>
                                        <td>{item.to}</td>
                                        <td>{item.item_name}</td>
                                        <td>{item.location_name}</td>
                                        <td>{item.game}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div>
                        <p>Populating sphere data...</p>
                    </div>
                )
            }
        </div>
    )
}

export default Sphere