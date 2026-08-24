import React from "react";
import { createRoot } from "react-dom/client";
import { EvidenceGraphApp } from "./new/app/AppRouter";
import "./new/styles/prototype.css";

createRoot(document.getElementById("root")).render(<EvidenceGraphApp />);
