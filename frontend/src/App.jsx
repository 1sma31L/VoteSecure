import { Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Services from './pages/Services'
import CreateElection from './pages/CreateElection'
import Dashboard from './pages/Dashboard'
import Voter from './pages/Voter'
import Results from './pages/Results'

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/services" element={<Services />} />
          <Route path="/create" element={<CreateElection />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/vote" element={<Voter />} />
          <Route path="/results" element={<Results />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
