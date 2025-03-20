document.addEventListener('alpine:init', () => {
    Alpine.data('progress', () => ({
        loading: true,
        error: null,
        progress: null,
        achievements: [],

        init() {
            if (Alpine.store('auth').isAuthenticated) {
                this.loadProgress();
            }
        },

        async loadProgress() {
            try {
                const token = Alpine.store('auth').getToken();
                if (!token) {
                    throw new Error('No authentication token');
                }

                this.loading = true;
                this.error = null;

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