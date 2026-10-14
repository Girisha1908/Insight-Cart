import { Route, Routes } from 'react-router-dom'
import Ask from './pages/Ask'
import Landing from './pages/Landing'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/ask" element={<Ask />} />
    </Routes>
  )
}
