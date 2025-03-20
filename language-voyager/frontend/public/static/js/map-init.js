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
                zoom: 12
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

            // Add Tokyo region boundary
            await this.addRegionPolygon({
                id: "tokyo",
                name: "Tokyo",
                center_lat: this.TOKYO_CENTER.latitude,
                center_lon: this.TOKYO_CENTER.longitude,
                bounds: {
                    north: 35.8187,
                    south: 35.5311,
                    east: 139.9224,
                    west: 139.5804
                }
            });

            return this.view;
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

        updateLocation(latitude, longitude) {
            if (this.view) {
                this.view.goTo({
                    center: [longitude, latitude],
                    zoom: 15
                });
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