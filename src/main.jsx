import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3500,
          style: {
            background: '#0f172a',
            color: '#f1f5f9',
            fontSize: '13px',
            borderRadius: '10px',
            border: '1px solid #1e293b',
          },
          success: { iconTheme: { primary: '#22c55e', secondary: '#0f172a' } },
          error:   { iconTheme: { primary: '#f43f5e', secondary: '#0f172a' } },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
)
