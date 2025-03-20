document.addEventListener('alpine:init', () => {
    Alpine.data('map', () => ({
        map: null,
        loading: true,
        error: null,

        async init() {
            // Wait for auth to be ready
            while (!this.$store.auth?.isAuthReady) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            if (!this.$store.auth.isAuthenticated) {
                window.location.href = '/';
                return;
            }

            try {
                // Wait for ArcGIS to be loaded (it exposes the require function)
                while (typeof require === 'undefined') {
                    await new Promise(resolve => setTimeout(resolve, 100));
                }

                // Wait for MapManager to be initialized
                while (!window.MapManager) {
                    await new Promise(resolve => setTimeout(resolve, 100));
                }

                const mapContainer = document.getElementById('map-container');
                if (!mapContainer) {
                    throw new Error('Map container not found');
                }

                await window.MapManager.initialize(mapContainer);
                this.loading = false;
                this.error = null;
            } catch (error) {
                console.error('Failed to initialize map:', error);
                this.error = error.message || 'Failed to initialize map';
                this.loading = false;
            }
        }
    }));
});