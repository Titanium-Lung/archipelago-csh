import { useState } from 'react'

function App() {
  const [file, setFile] = useState(null) 
  const [message, setMessage] = useState("")
  // const [serverInfo, setServerInfo] = useState(null)
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

  return (
    <div>
      <h1>Archipelago Host</h1>
      <input type="file" accept=".archipelago" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button>
      <p>{message}</p>
      {
        port != "" && (
          <div>
            <p>Port: {port}</p>
          </div>
        )
      }
    </div>
  )
}

export default App
