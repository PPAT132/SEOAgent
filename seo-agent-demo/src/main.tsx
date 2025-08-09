import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './index.css';
import App from './App';
import LighthousePage from './LighthousePage';

createRoot(document.getElementById('root') as HTMLElement).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/optimizer" element={<App />} />
        <Route path="/lighthouse" element={<LighthousePage />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>
);