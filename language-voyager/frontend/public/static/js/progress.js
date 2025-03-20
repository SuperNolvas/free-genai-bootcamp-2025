document.addEventListener('alpine:init', () => {
    Alpine.data('progress', () => ({
        stats: null,
        loading: true,
        error: null,

        init() {
            this.loadProgress();
        },

        async loadProgress() {
            try {
                const token = localStorage.getItem('token');
                if (!token) throw new Error('No authentication token');

                const response = await fetch('/api/v1/progress', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    this.stats = data;
                    
                    // Hide the loading placeholder
                    document.getElementById('progress-placeholder').style.display = 'none';
                    
                    // Cache progress data for offline access
                    localStorage.setItem('cached_progress', JSON.stringify(data));
                } else {
                    throw new Error('Failed to load progress');
                }
            } catch (err) {
                console.error('Progress loading error:', err);
                this.error = 'Failed to load progress data';
                
                // Try to load cached data if offline
                const cachedData = localStorage.getItem('cached_progress');
                if (cachedData) {
                    this.stats = JSON.parse(cachedData);
                }
            } finally {
                this.loading = false;
            }
        },

        formatPercent(value) {
            return `${Math.round(value * 100)}%`;
        }
    }));
});