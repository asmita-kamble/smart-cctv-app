import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// Global error handler to catch any unhandled errors
window.addEventListener('error', (event) => {
  console.error('=== GLOBAL ERROR CAUGHT ===');
  console.error('Error message:', event.message);
  console.error('Error source:', event.filename);
  console.error('Error line:', event.lineno);
  console.error('Error column:', event.colno);
  console.error('Error object:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('=== UNHANDLED PROMISE REJECTION ===');
  console.error('Reason:', event.reason);
  console.error('Promise:', event.promise);
});

// Log when app starts
console.log('=== APP STARTING ===');
console.log('React version:', React.version);
console.log('Current URL:', window.location.href);

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

