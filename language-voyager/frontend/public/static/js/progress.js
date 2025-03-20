document.addEventListener('alpine:init', () => {
    Alpine.data('progress', () => ({
        loading: true,
        error: null,
        progress: null,
        achievements: [],

        init() {
            // Load progress only if we're already authenticated
            if (window.authStore && window.authStore.isAuthenticated) {
                this.loadProgress();
            }
        },

        async loadProgress() {
            if (!Alpine.store('auth').isAuthenticated) return;
            
            try {
                this.loading = true;
                this.error = null;
                
                const token = Alpine.store('auth').getToken();
                if (!token) {
                    throw new Error('No authentication token');
                }

                const response = await fetch('/api/v1/progress', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (!response.ok) {
                    throw new Error('Failed to load progress');
                }

                const data = await response.json();
                this.progress = data.progress;
                this.achievements = data.achievements || [];
            } catch (error) {
                console.error('Progress loading error:', error);
                this.error = error.message;
            } finally {
                this.loading = false;
            }
        }
    }));
});