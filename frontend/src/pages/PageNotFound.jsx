import React from "react"
import { Navbar } from "../Navbar"

function PageNotFound() {
    return (
        <div>
            <title>Page Not Found</title>
            <Navbar full={false}></Navbar>
            <div className="text-center">
                <h2>404 Error</h2>
                <p>Oops! The page you're looking for does not exist.</p>
            </div>
        </div>
    )
}

export default PageNotFound