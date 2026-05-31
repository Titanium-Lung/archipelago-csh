import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Link } from "react-router-dom"
import logo from "../assets/CSH Archipelago Logo.svg"

function Home() {
    const navigate = useNavigate()

    const [file, setFile] = useState(null) 
    const [message, setMessage] = useState("")
    const [port, setPort] = useState("")

    function handleFileChange(event) {
        setFile(event.target.files[0])
    }

    async function handleUpload() {
        if (!file) {
            setMessage("Please select a file first.")
            return
        }
        
        try {
            const formData = new FormData()
            formData.append("file", file)

            const response = await fetch("http://localhost:5001/upload", {
                method: "POST",
                body: formData
            })

            const result = await response.json()


            if (response.ok) {
                setMessage("Server started!")
                setPort(result.port)
            } else {
                setMessage("Error: " + result.error)
            }
        } catch (error) {
            setMessage("Error: " + error.message)
        }
    }

    function sendToRoom() {
        navigate("/room")
    }

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
                            <a className="nav-link" href="/">Home <span className="sr-only">(current)</span></a>
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
            <div style={{textAlign: 'center'}}>
                <h1>Archipelago Host</h1>
                <div className="form-group">
                    <input type="file" accept=".zip" onChange={handleFileChange} className="form-control-file" id="exampleInputFile" aria-describedby="fileHelp" />
                    <button className="btn btn-primary" onClick={handleUpload}>Upload</button>
                    <br></br>
                    <small id="fileHelp" className="form-text text-muted">Upload the zip file of your generated multiworld</small>
                </div>
                <p>{message}</p>
                {
                    port != "" && (
                    <div>
                        <p>Port: {port}</p> 
                        <button className="btn btn-primary" onClick={sendToRoom}>Go to room</button>
                    </div>
                    )
                }
            </div>
        </div>
    )
}

export default Home
