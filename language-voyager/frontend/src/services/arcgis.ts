import ArcGISMap from '@arcgis/core/Map';
import MapView from '@arcgis/core/views/MapView';
import Graphic from '@arcgis/core/Graphic';
import Point from '@arcgis/core/geometry/Point';
import SimpleMarkerSymbol from '@arcgis/core/symbols/SimpleMarkerSymbol';
import Polygon from '@arcgis/core/geometry/Polygon';
import SimpleFillSymbol from '@arcgis/core/symbols/SimpleFillSymbol';
import { POI, LocationUpdate } from '@/types/api';

interface Region {
  id: string;
  name: string;
  center_lat: number;
  center_lon: number;
  bounds?: {
    north: number;
    south: number;
    east: number;
    west: number;
  };
}

type LocationChangeListener = (location: LocationUpdate) => void;

export class ArcGISMapService {
  private map: ArcGISMap | null = null;
  private view: MapView | null = null;
  private locationMarker: Graphic | null = null;
  private poiMarkers = new Map<string, Graphic>();
  private regionPolygons = new Map<string, Graphic>();
  private locationListeners: LocationChangeListener[] = [];

  // Tokyo coordinates and bounds
  private TOKYO_CENTER = {
    latitude: 35.6762,
    longitude: 139.6503
  };

  private TOKYO_BOUNDS = {
    north: 35.8187,
    south: 35.5311,
    east: 139.9224,
    west: 139.5804
  };

  async initialize(container: HTMLDivElement) {
    this.map = new ArcGISMap({
      basemap: 'streets-vector'
    });

    this.view = new MapView({
      container,
      map: this.map,
      center: [this.TOKYO_CENTER.longitude, this.TOKYO_CENTER.latitude],
      zoom: 12,
      constraints: {
        geometry: {
          type: "extent",
          xmin: this.TOKYO_BOUNDS.west,
          ymin: this.TOKYO_BOUNDS.south,
          xmax: this.TOKYO_BOUNDS.east,
          ymax: this.TOKYO_BOUNDS.north,
          spatialReference: { wkid: 4326 }
        }
      }
    });

    await this.view.when(); // Wait for view to be ready

    // Initialize location marker with a random position
    const initialLat = this.TOKYO_BOUNDS.south + 
      (Math.random() * (this.TOKYO_BOUNDS.north - this.TOKYO_BOUNDS.south));
    const initialLon = this.TOKYO_BOUNDS.west + 
      (Math.random() * (this.TOKYO_BOUNDS.east - this.TOKYO_BOUNDS.west));

    const point = new Point({
      longitude: initialLon,
      latitude: initialLat,
      spatialReference: { wkid: 4326 }
    });

    const locationSymbol = new SimpleMarkerSymbol({
      color: '#2196f3',
      outline: {
        color: '#ffffff',
        width: 2
      },
      size: 12
    });

    this.locationMarker = new Graphic({
      geometry: point,
      symbol: locationSymbol
    });
    
    this.view.graphics.add(this.locationMarker);

    // Add Tokyo region boundary
    await this.addRegionPolygon({
      id: "tokyo",
      name: "Tokyo",
      center_lat: this.TOKYO_CENTER.latitude,
      center_lon: this.TOKYO_CENTER.longitude,
      bounds: this.TOKYO_BOUNDS
    });

    // Set view to show the initial location
    this.updateLocation(initialLat, initialLon);

    return this.view;
  }

  async setRandomLocation() {
    // Generate random coordinates within Tokyo bounds
    const latitude = this.TOKYO_BOUNDS.south + 
      (Math.random() * (this.TOKYO_BOUNDS.north - this.TOKYO_BOUNDS.south));
    const longitude = this.TOKYO_BOUNDS.west + 
      (Math.random() * (this.TOKYO_BOUNDS.east - this.TOKYO_BOUNDS.west));

    // Update marker position
    this.updateLocationMarker({
      latitude,
      longitude,
      accuracy: 10
    });

    return { latitude, longitude };
  }

  onLocationChange(listener: LocationChangeListener) {
    this.locationListeners.push(listener);
    return () => {
      this.locationListeners = this.locationListeners.filter(l => l !== listener);
    };
  }

  private notifyLocationChange(location: LocationUpdate) {
    this.locationListeners.forEach(listener => listener(location));
  }

  private updateLocation(latitude: number, longitude: number) {
    if (this.view) {
      this.view.goTo({
        center: [longitude, latitude],
        zoom: 15
      });
    }
  }

  updateLocationMarker(location: LocationUpdate) {
    if (!this.view || !location.latitude || !location.longitude) return;

    const point = new Point({
      longitude: location.longitude,
      latitude: location.latitude,
      spatialReference: { wkid: 4326 }
    });

    if (this.locationMarker) {
      this.locationMarker.geometry = point;
    }

    this.updateLocation(location.latitude, location.longitude);
    this.notifyLocationChange(location);
  }

  addPOI(poi: POI) {
    if (!this.map || !this.view) return;

    const point = new Point({
      longitude: poi.lon,
      latitude: poi.lat,
      spatialReference: { wkid: 4326 }
    });

    const symbol = new SimpleMarkerSymbol({
      color: '#4caf50',
      outline: {
        color: '#ffffff',
        width: 1
      },
      size: 10
    });

    const graphic = new Graphic({
      geometry: point,
      symbol,
      attributes: {
        id: poi.id,
        name: poi.name,
        type: poi.type
      },
      popupTemplate: {
        title: poi.local_name || poi.name,
        content: [
          {
            type: "fields",
            fieldInfos: [
              {
                fieldName: "type",
                label: "Type"
              }
            ]
          }
        ]
      }
    });

    this.view.graphics.add(graphic);
    this.poiMarkers.set(poi.id, graphic);
  }

  addRegionPolygon(region: Region & { bounds?: { north: number; south: number; east: number; west: number } }) {
    if (!this.view) return;

    const polygonGeometry = {
      type: "polygon" as const,
      rings: [
        [
          [region.bounds?.west || region.center_lon - 0.1, region.bounds?.south || region.center_lat - 0.1],
          [region.bounds?.east || region.center_lon + 0.1, region.bounds?.south || region.center_lat - 0.1],
          [region.bounds?.east || region.center_lon + 0.1, region.bounds?.north || region.center_lat + 0.1],
          [region.bounds?.west || region.center_lon - 0.1, region.bounds?.north || region.center_lat + 0.1],
          [region.bounds?.west || region.center_lon - 0.1, region.bounds?.south || region.center_lat - 0.1]
        ]
      ],
      spatialReference: { wkid: 4326 }
    };

    const symbol = new SimpleFillSymbol({
      color: [51, 51, 204, 0.2],
      outline: {
        color: [51, 51, 204],
        width: 1
      }
    });

    const graphic = new Graphic({
      geometry: polygonGeometry,
      symbol,
      attributes: {
        id: region.id,
        name: region.name
      }
    });

    this.regionPolygons.set(region.id, graphic);
    this.view.graphics.add(graphic);
  }

  removePOI(poiId: string) {
    const marker = this.poiMarkers.get(poiId);
    if (marker && this.view) {
      this.view.graphics.remove(marker);
      this.poiMarkers.delete(poiId);
    }
  }

  removeRegion(regionId: string) {
    const polygon = this.regionPolygons.get(regionId);
    if (polygon && this.view) {
      this.view.graphics.remove(polygon);
      this.regionPolygons.delete(regionId);
    }
  }

  clearAll() {
    if (this.view) {
      this.view.graphics.removeAll();
      this.poiMarkers.clear();
      this.regionPolygons.clear();
      
      // Re-add location marker
      if (this.locationMarker) {
        this.view.graphics.add(this.locationMarker);
      }
    }
  }

  refresh() {
    if (this.view) {
      this.view.goTo({
        center: [this.TOKYO_CENTER.longitude, this.TOKYO_CENTER.latitude],
        zoom: 12
      });
    }
  }

  destroy() {
    if (this.view) {
      this.view.destroy();
    }
  }
}

export const arcgisService = new ArcGISMapService();
export default arcgisService;