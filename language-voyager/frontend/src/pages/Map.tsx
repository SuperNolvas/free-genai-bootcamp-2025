import React, { useEffect, useState } from 'react';
import MapManager from '../services/arcgis';
import { LocationTracker } from '../components/map/LocationTracker';

export default function Map() {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Listen for map initialization from Alpine.js
    const handleMapReady = () => {
      setIsLoading(false);
    };

    window.addEventListener('map:ready', handleMapReady);
    
    // If map is already initialized, update state
    if (window.MapManager?.view) {
      setIsLoading(false);
    }

    return () => {
      window.removeEventListener('map:ready', handleMapReady);
    };
  }, []);

  return (
    <div className="relative w-full h-full">
      {isLoading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-white bg-opacity-90 z-10">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-gray-700">Loading map...</p>
        </div>
      )}
      <LocationTracker />
    </div>
  );
}