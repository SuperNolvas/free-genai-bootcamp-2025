import React from 'react';
import ReactDOM from 'react-dom/client';
import Map from './pages/Map';
import { ArcGISMapService } from './services/arcgis';

// Create and export map manager instance
const MapManager = new ArcGISMapService();
(window as any).MapManager = MapManager;

// Initialize map components in the overlay container
const overlayContainer = document.getElementById('map-overlay-container');
if (overlayContainer) {
  const root = ReactDOM.createRoot(overlayContainer);
  root.render(
    <React.StrictMode>
      <Map />
    </React.StrictMode>
  );
}

export default MapManager;
