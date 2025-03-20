document.addEventListener('alpine:init', () => {
    Alpine.data('map', () => ({
        map: null,
        loading: true,
        error: null,
        regions: [],
        selectedRegion: null,
        view: null,
        initialized: false,

        async init() {
            // Wait for auth to be ready
            while (!this.$store.auth.isAuthReady) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            if (!this.$store.auth.isAuthenticated) {
                window.location.href = '/';
                return;
            }

            await this.initializeMap();
        },

        // ...rest of existing code...