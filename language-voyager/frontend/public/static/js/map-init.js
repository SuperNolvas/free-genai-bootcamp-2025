// Wait for ArcGIS API to load
require(['esri/Map', 'esri/views/MapView', 'esri/Graphic', 'esri/geometry/Point', 'esri/symbols/SimpleMarkerSymbol', 'esri/symbols/SimpleFillSymbol'], 
(Map, MapView, Graphic, Point, SimpleMarkerSymbol, SimpleFillSymbol) => {
    
    class ArcGISMapService {
        constructor() {
            this.map = null;
            this.view = null;
            this.locationMarker = null;
            this.poiMarkers = new Map(); // This is a JavaScript Map
            this.regionPolygons = new Map();
            this.locationListeners = [];
            this.chatReady = false;
            this.initialLocation = null;
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

            // Set view to show the initial location and get details
            this.updateLocation(initialLat, initialLon);
            const initialDetails = await this.getLocationDetails(initialLat, initialLon);
            
            // Notify of initial location with details
            await this.notifyLocationChange({
                latitude: initialLat,
                longitude: initialLon,
                accuracy: 10,
                ...initialDetails
            });

            return this.view;
        }

        async setRandomLocation() {
            const latitude = this.TOKYO_BOUNDS.south + 
                (Math.random() * (this.TOKYO_BOUNDS.north - this.TOKYO_BOUNDS.south));
            const longitude = this.TOKYO_BOUNDS.west + 
                (Math.random() * (this.TOKYO_BOUNDS.east - this.TOKYO_BOUNDS.west));

            await this.updateLocationMarker({
                latitude,
                longitude,
                accuracy: 10
            });

            return { latitude, longitude };
        }

        updateLocation(latitude, longitude) {
            if (this.view) {
                this.view.goTo({
                    center: [longitude, latitude],
                    zoom: 15
                });
            }
        }

        async updateLocationMarker(location) {
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

            // Always fetch location details
            const details = await this.getLocationDetails(location.latitude, location.longitude);
            
            // Notify of location change with the fetched details
            await this.notifyLocationChange({
                ...location,
                ...details
            });
        }

        onLocationChange(listener) {
            this.locationListeners.push(listener);
            return () => {
                this.locationListeners = this.locationListeners.filter(l => l !== listener);
            };
        }

        async notifyLocationChange(location) {
            // Ensure we have all required fields
            const locationDetail = {
                ...location,
                type: location.type || this.determinePOIType(location),
                region: 'Tokyo',
                name: location.name
            };

            // Log the location details being sent
            console.log('Notifying location change:', locationDetail);

            // Dispatch custom event for the chat interface
            window.dispatchEvent(new CustomEvent('location:updated', {
                detail: locationDetail
            }));

            // Notify existing listeners
            this.locationListeners.forEach(listener => listener(locationDetail));
        }

        determinePOIType(location) {
            if (!this.view) return 'area';
            
            if (this.view.zoom >= 19) {
                return 'building';
            } else if (this.view.zoom >= 17) {
                return 'street';
            } else if (this.view.zoom >= 13) {
                return 'neighborhood';
            } else {
                return 'area';
            }
        }

        getLocationName(location) {
            try {
                // Format coordinates nicely
                const lat = Math.abs(location.latitude).toFixed(4) + '°' + (location.latitude >= 0 ? 'N' : 'S');
                const lon = Math.abs(location.longitude).toFixed(4) + '°' + (location.longitude >= 0 ? 'E' : 'W');
                
                // First check POI markers if we have any
                if (this.poiMarkers.size > 0) {
                    for (const [_, marker] of this.poiMarkers) {
                        if (!marker?.geometry) continue;
                        
                        if (this.isNearby(location, {
                            latitude: marker.geometry.latitude,
                            longitude: marker.geometry.longitude
                        })) {
                            return marker.attributes?.name || `${lat}, ${lon}`;
                        }
                    }
                }
                
                // If no POI is found, return formatted coordinates
                return `${lat}, ${lon}`;
            } catch (error) {
                console.warn('Error checking POI markers:', error);
                return `${location.latitude.toFixed(4)}°N, ${location.longitude.toFixed(4)}°E`;
            }
        }

        isNearby(loc1, loc2, threshold = 0.001) { // roughly 100 meters
            if (!loc1 || !loc2) return false;
            return Math.abs(loc1.latitude - loc2.latitude) < threshold &&
                   Math.abs(loc1.longitude - loc2.longitude) < threshold;
        }

        async getLocationDetails(latitude, longitude) {
            try {
                console.log('Fetching location details for:', latitude, longitude);
                const response = await fetch(`/api/v1/map/location/details?lat=${latitude}&lon=${longitude}`);
                if (!response.ok) {
                    throw new Error('Failed to fetch location details');
                }
                const data = await response.json();
                console.log('Got location details:', data);
                
                // Return the location details, ensuring we have the Japanese name
                return {
                    name: data.local_name || data.name,  // Prefer Japanese name
                    description: data.description || '',
                    type: data.type || this.determinePOIType({ latitude, longitude }),
                    region_specific_customs: data.customs || {}
                };
            } catch (error) {
                console.warn('Error fetching location details:', error);
                return {
                    name: this.getLocationName({ latitude, longitude }),
                    description: '',
                    type: this.determinePOIType({ latitude, longitude }),
                    region_specific_customs: {}
                };
            }
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