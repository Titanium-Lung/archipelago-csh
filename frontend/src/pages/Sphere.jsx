import { useEffect, useState } from "react"
import logo from "../assets/CSH Archipelago Logo.svg"

function Sphere() {
    const [sphereData, setSphereData] = useState([])
    const [filteredData, setFilteredData] = useState([])
    const [sortedColumn, setSortedColumn] = useState(localStorage.getItem("sortedColumn") || null)
    const [sortDirection, setSortDirection] = useState(localStorage.getItem("sortDirection") || "asc")
    const [filter, setFilter] = useState('')

    useEffect(() => {
        async function fetchSpheres() {
            const response = await fetch("http://localhost:5001/spheres", {
                method: "GET"
            })

            const result = await response.json()

            if (response.ok) {
                console.log("Successfully fetched")
                setSphereData(result.items)
                setFilteredData(result.items)
            }
        }
        fetchSpheres()
    }, [])

    useEffect(() => {
        if (sortedColumn) {
            localStorage.setItem("sortedColumn", sortedColumn)
        }
    }, [sortedColumn])

    useEffect(() => {
        if (sortDirection) {
            localStorage.setItem("sortDirection", sortDirection)
        }
    }, [sortDirection])

    function setSort(column) {
        if (sortedColumn === column) {
            console.log("The current direction is the same")
            setSortDirection(sortDirection === "asc" ? "desc" : "asc")
        } else {
            setSortedColumn(column)
            setSortDirection("asc")
        }
    }

    useEffect(() => {
        const filteredSpheres = []

        sphereData.forEach((item) => {
            if (item["item_name"].toLowerCase().includes(filter.toLowerCase()) ||
                    item["location_name"].toLowerCase().includes(filter.toLowerCase()) ||
                    String(item["sphere"]).includes(filter.toLowerCase()) ||
                    item["from"].toLowerCase().includes(filter.toLowerCase()) ||
                    item["to"].toLowerCase().includes(filter.toLowerCase()) ||
                    item["game"].toLowerCase().includes(filter.toLowerCase())) {
                filteredSpheres.push(item)
            }
        })

        setFilteredData(filteredSpheres)
    }, [filter])

    const sortedSpheres = sortedColumn ? [...filteredData].sort((a, b) => {
        if (a[sortedColumn] < b[sortedColumn]) return sortDirection === "asc" ? -1 : 1
        if (a[sortedColumn] > b[sortedColumn]) return sortDirection === "asc" ? 1 : -1
        return 0
    }) : filteredData

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
            <h1 style={{textAlign: 'center'}}>Sphere tracker</h1>
            <p className="mx-3">This tracker lists already found locations by their logical access sphere. 
                It ignores items that cannot be sent and will therefore differ from the sphere numbers in the spoiler playthrough.
                This tracker will automatically update itself periodically.</p>
            <div className="mx-md-5 m-3">
                <input type="text" id="input" name="search" placeholder="Search" value={filter} onChange={e => setFilter(e.target.value)} />
            </div>
            {
                sphereData.length > 0 ? (
                    <div className="d-flex justify-content-center mx-md-5">
                        <table className="table table-hover">
                            <thead>
                                <tr className="table-primary">
                                    <th onClick={() => setSort("sphere")} style={{cursor: 'pointer'}}>Sphere</th>
                                    <th onClick={() => setSort("from")} style={{cursor: 'pointer'}}>Finder</th>
                                    <th onClick={() => setSort("to")} style={{cursor: 'pointer'}}>Receiver</th>
                                    <th onClick={() => setSort("item_name")} style={{cursor: 'pointer'}}>Item</th>
                                    <th onClick={() => setSort("location_name")} style={{cursor: 'pointer'}}>Location</th>
                                    <th onClick={() => setSort("game")} style={{cursor: 'pointer'}}>Game</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sortedSpheres.map(item => (
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
                    <div className="d-flex justify-content-center mx-md-5">
                        <p>No received items</p>
                    </div>
                )
            }
        </div>
    )
}

export default Sphere