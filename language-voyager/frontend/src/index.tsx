import React from 'react';
import ReactDOM from 'react-dom/client';
import Map from './pages/Map';

// Initialize map components in the container provided by Alpine.js
const mapContainer = document.getElementById('map-container');
if (mapContainer) {
  const root = ReactDOM.createRoot(mapContainer);
  root.render(
    <React.StrictMode>
      <Map />
    </React.StrictMode>
  );
}
