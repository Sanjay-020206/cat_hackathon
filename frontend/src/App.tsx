import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { LiveOperation } from "./pages/LiveOperation";
import { SafetyCenter } from "./pages/SafetyCenter";
import { ShiftIntelligence } from "./pages/ShiftIntelligence";
import { TrainingHub } from "./pages/TrainingHub";

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/live" element={<LiveOperation />} />
          <Route path="/safety" element={<SafetyCenter />} />
          <Route path="/training" element={<TrainingHub />} />
          <Route path="/shift" element={<ShiftIntelligence />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
