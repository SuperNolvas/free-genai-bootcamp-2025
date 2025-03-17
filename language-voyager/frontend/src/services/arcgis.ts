import Map from '@arcgis/core/Map';
import MapView from '@arcgis/core/views/MapView';
import Graphic from '@arcgis/core/Graphic';
import Point from '@arcgis/core/geometry/Point';
import SimpleMarkerSymbol from '@arcgis/core/symbols/SimpleMarkerSymbol';
import Polygon from '@arcgis/core/geometry/Polygon';
import SimpleFillSymbol from '@arcgis/core/symbols/SimpleFillSymbol';
import { POI, Region } from '../types/api';
import { store } from '../store/store';

class ArcGISService {
  private map: Map | null = null;
  private view: MapView | null = null;
  private locationMarker: Graphic | null = null;
  private poiMarkers: Map<string, Graphic> = new Map();
  private regionPolygons: Map<string, Graphic> = new Map();

  async initialize(container: HTMLDivElement) {
    this.map = new Map({
      basemap: 'streets-vector'
    });

    this.view = new MapView({
      container,
      map: this.map,
      zoom: 15
    });

    // Create location marker symbol
    const locationSymbol = new SimpleMarkerSymbol({
      color: '#2196f3',
      outline: {
        color: '#ffffff',
        width: 2
      },
      size: 12
    });

    // Initialize location marker (hidden initially)
    this.locationMarker = new Graphic({
      symbol: locationSymbol
    });
    this.view.graphics.add(this.locationMarker);

    // Subscribe to location updates
    store.subscribe(() => {
      const state = store.getState();
      const location = state.map.currentLocation;
      
      if (location) {
        this.updateLocation(location.latitude, location.longitude);
      }
    });

    return this.view;
  }

  updateLocation(latitude: number, longitude: number) {
    if (!this.locationMarker) return;

    const point = new Point({
      longitude,
      latitude,
      spatialReference: { wkid: 4326 }
    });

    this.locationMarker.geometry = point;

    // Center map on new location
    this.view?.goTo({
      target: point,
      zoom: this.view.zoom
    });
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

  addRegion(region: Region) {
    if (!this.map || !this.view) return;

    // Convert region bounds to polygon (simplified for example)
    // In real implementation, region should include proper boundary coordinates
    const polygon = new Polygon({
      rings: [
        // Example polygon - should be replaced with actual region boundaries
        [region.center_lon - 0.1, region.center_lat - 0.1],
        [region.center_lon + 0.1, region.center_lat - 0.1],
        [region.center_lon + 0.1, region.center_lat + 0.1],
        [region.center_lon - 0.1, region.center_lat + 0.1],
        [region.center_lon - 0.1, region.center_lat - 0.1]
      ],
      spatialReference: { wkid: 4326 }
    });

    const symbol = new SimpleFillSymbol({
      color: [76, 175, 80, 0.2],
      outline: {
        color: '#4caf50',
        width: 2
      }
    });

    const graphic = new Graphic({
      geometry: polygon,
      symbol,
      attributes: {
        id: region.id,
        name: region.name,
        language: region.language
      }
    });

    this.view.graphics.add(graphic);
    this.regionPolygons.set(region.id, graphic);
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

  destroy() {
    if (this.view) {
      this.view.destroy();
    }
  }
}

export const arcgisService = new ArcGISService();
export default arcgisService;