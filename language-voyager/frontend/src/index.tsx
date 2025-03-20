import React from 'react';
import ReactDOM from 'react-dom/client';
import Map from './pages/Map';
import { ArcGISMapService } from './services/arcgis';

// Create and export map manager instance
const MapManager = new ArcGISMapService();
(window as any).MapManager = MapManager;

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

export default MapManager;
