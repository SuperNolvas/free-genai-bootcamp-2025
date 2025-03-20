// Wait for ArcGIS API to load
require(['esri/Map', 'esri/views/MapView', 'esri/Graphic', 'esri/geometry/Point', 'esri/symbols/SimpleMarkerSymbol', 'esri/symbols/SimpleFillSymbol'], 
(Map, MapView, Graphic, Point, SimpleMarkerSymbol, SimpleFillSymbol) => {
    
    class ArcGISMapService {
        constructor() {
            this.map = null;
            this.view = null;
            this.locationMarker = null;
            this.poiMarkers = new Map();
            this.regionPolygons = new Map();
            this.locationListeners = [];
            this.TOKYO_CENTER = {
                latitude: 35.6762,
                longitude: 139.6503
            };
            this.TOKYO_BOUNDS = {
                north: 35.8187,
                south: 35.5311,
                east: 139.9224,
                west: 139.5804
            };
        }

        async initialize(container) {
            // Create the map
            this.map = new Map({
                basemap: 'streets-vector'
            });

            // Create the view
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

            await this.view.when();

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
            const latitude = this.TOKYO_BOUNDS.south + 
                (Math.random() * (this.TOKYO_BOUNDS.north - this.TOKYO_BOUNDS.south));
            const longitude = this.TOKYO_BOUNDS.west + 
                (Math.random() * (this.TOKYO_BOUNDS.east - this.TOKYO_BOUNDS.west));

            this.updateLocationMarker({
                latitude,
                longitude,
                accuracy: 10
            });

            return { latitude, longitude };
        }

        updateLocationMarker(location) {
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

        updateLocation(latitude, longitude) {
            if (this.view) {
                this.view.goTo({
                    center: [longitude, latitude],
                    zoom: 15
                });
            }
        }

        onLocationChange(listener) {
            this.locationListeners.push(listener);
            return () => {
                this.locationListeners = this.locationListeners.filter(l => l !== listener);
            };
        }

        notifyLocationChange(location) {
            this.locationListeners.forEach(listener => listener(location));
        }

        async addRegionPolygon(region) {
            if (!this.view) return;

            const polygonGeometry = {
                type: "polygon",
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

        clearAll() {
            if (this.view) {
                this.view.graphics.removeAll();
                this.poiMarkers.clear();
                this.regionPolygons.clear();
                
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
    }

    // Initialize and expose MapManager globally
    window.MapManager = new ArcGISMapService();
});