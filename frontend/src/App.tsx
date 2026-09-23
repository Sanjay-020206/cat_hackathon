import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { Expertise } from "./pages/Expertise";
import { LiveOperation } from "./pages/LiveOperation";
import { SafetyCenter } from "./pages/SafetyCenter";
import { ShiftIntelligence } from "./pages/ShiftIntelligence";
import { SiteMap } from "./pages/SiteMap";
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
          <Route path="/expertise" element={<Expertise />} />
          <Route path="/site-map" element={<SiteMap />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
