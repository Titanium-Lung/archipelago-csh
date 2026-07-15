import google_logo from "../assets/Google_logo.svg"
import csh_logo from "../assets/CSH_logo.png"
import { Navbar } from "../Navbar"

function Login() {

    return (
        <div>
            <title>Login</title>
            <Navbar full={false}></Navbar>
            <div className="row justify-content-center mt-5">
                <div className="col-auto text-center">
                    <h2>Login with CSH</h2>
                    <a href={`${import.meta.env.VITE_BACKEND_URL}/login`}>
                        <img src={csh_logo} style={{ width: "400px" }} className="rounded" alt="CSH logo" />
                    </a>
                </div>
                <div className="col-auto text-center" style={{ margin: "0 100px"}}>
                    <h2>Login with Google</h2>
                    <a href={`${import.meta.env.VITE_BACKEND_URL}/googlelogin`}>
                        <img src={google_logo} style={{ width: "400px" }} alt="Google logo" />
                    </a>
                </div>
            </div>
        </div>
    )
}

export default Login