import { createContext, useContext, useState, useEffect } from "react"

const UserContext = createContext(null)

export function UserProvider({ children }) {
    const [user, setUser] = useState(null)

    useEffect(() => {
        async function fetchUser() {
            const response = await fetch("http://localhost:5001/user", {
                credentials: "include"
            })
            if (response.ok) {
                const data = await response.json()
                setUser(data)
            } else {
                window.location.href = "http://localhost:5001/login"
            }
        }
        fetchUser()
    }, [])

    return (
        <UserContext.Provider value={user}>
            {children}
        </UserContext.Provider>
    )

}

export function useUser() {
    return useContext(UserContext)
}