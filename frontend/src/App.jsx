import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Employees from "./pages/Employees";
import FaceRegister from "./pages/FaceRegister";
// import FaceAttendance from "./pages/FaceAttendance";
import Reports from "./pages/Reports"

import "./App.css";

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/employees" element={<Employees />} />
          <Route path="/face-register" element={<FaceRegister />} />
          <Route path="/reports" element={<Reports />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

// export default function App() {
//   return (
//     <BrowserRouter>
//       <Layout>
//         <Routes>
//           <Route path="/" element={<Dashboard />} />
//           <Route path="/employees" element={<Employees />} />
//           <Route path="/face-register" element={<FaceRegister />} />
//           <Route path="/face-attendance" element={<FaceAttendance />} />
//           <Route path="/reports" element={<Reports />} />
//         </Routes>
//       </Layout>
//     </BrowserRouter>
//   );
// }
