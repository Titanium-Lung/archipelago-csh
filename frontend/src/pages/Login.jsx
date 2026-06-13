import logo from "../assets/CSH Archipelago Logo.svg"
import csh_logo from "../assets/CSH_logo.png"

function Login() {

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
                </div>
            </nav>
            <div>
                <div className="text-center">
                    <h2>Login with CSH</h2>
                </div>
                <div>
                    <a href="http://localhost:5001/login">
                        <img src={csh_logo} style={{ width: "400px" }} className="rounded mx-auto d-block" alt="CSH logo" />
                    </a>
                </div>
            </div>
        </div>
    )
}

export default Login