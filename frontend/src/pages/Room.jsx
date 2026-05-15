import { useLocation } from "react-router-dom"

function Room() {
    const location = useLocation()
    const { port, filler } = location.state

    return (
        <div>
            <h1>Room</h1>
            <p>Your room's port is {port}</p>
            <p>Your filler  is {filler}</p>
        </div>
    )
}

export default Room