import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import App from "./App";
import ScreenPage from "./components/ScreenPage";
import ProtocolsPage from "./components/ProtocolsPage";
import ProtocolDetailPage from "./components/ProtocolDetailPage";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<ScreenPage />} />
          <Route path="protocols" element={<ProtocolsPage />} />
          <Route path="protocols/:id" element={<ProtocolDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
