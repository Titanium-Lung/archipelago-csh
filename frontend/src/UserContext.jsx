import { createContext, useContext, useState, useEffect } from "react"

const UserContext = createContext(null)

export function UserProvider({ children }) {
    const [user, setUser] = useState(null)

    useEffect(() => {
        async function fetchUser() {
            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/user`, {
                credentials: "include"
            })
            if (response.ok) {
                const data = await response.json()
                setUser(data)
            } else if (window.location.pathname !== '/login') {
                window.location.href = "https://archipelago-dev.cs.house/login"
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