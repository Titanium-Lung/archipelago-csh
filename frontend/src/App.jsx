import { useState } from 'react'

function App() {
  const [file, setFile] = useState(null) 
  const [message, setMessage] = useState("")
  const [serverInfo, setServerInfo] = useState(null)

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

      const data = await response.json

      if (response.ok) {
        setMessage("Server started!")
        setServerInfo(data)
      } else {
        setMessage("Error: " + data.error)
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
      {serverInfo && (
        <div>
          <p>World: {serverInfo.filename}</p>
          <p>Players connect to: localhost:{serverInfo.port}</p>
        </div>
      )}
    </div>
  )
}

export default App
