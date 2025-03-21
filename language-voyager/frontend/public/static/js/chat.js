document.addEventListener('alpine:init', () => {
    Alpine.data('chat', () => ({
        messages: [],
        newMessage: '',
        currentLocation: null,
        locationContext: null,
        loading: false,

        init() {
            // Listen for location updates from MapManager
            window.addEventListener('location:updated', this.handleLocationUpdate.bind(this));
        },

        destroy() {
            window.removeEventListener('location:updated', this.handleLocationUpdate.bind(this));
        },

        handleLocationUpdate(event) {
            const location = event.detail;
            this.currentLocation = `${location.type}: ${location.name}`;
            this.locationContext = {
                poi_type: location.type,
                formality_level: 'polite',
                dialect: 'standard',
                difficulty_level: 50,
                region_specific_customs: {},
                location_name: location.name,
                coordinates: {
                    lat: location.latitude,
                    lng: location.longitude
                }
            };

            // Add system message about new location
            this.messages.push({
                id: Date.now(),
                role: 'system',
                content: `Location changed to: ${location.name} (${location.type})`
            });
        },

        async sendMessage() {
            if (!this.newMessage.trim() || this.loading) return;
            
            const token = localStorage.getItem('token');
            const userMessage = this.newMessage.trim();
            
            // Add user message
            this.messages.push({
                id: Date.now(),
                role: 'user',
                content: userMessage
            });
            
            this.newMessage = '';
            this.loading = true;

            try {
                const response = await fetch('/api/v1/conversation/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        messages: [{
                            role: 'user',
                            content: userMessage
                        }],
                        context: this.locationContext || {
                            poi_type: 'area',
                            formality_level: 'polite',
                            dialect: 'standard',
                            difficulty_level: 50,
                            region_specific_customs: {}
                        }
                    })
                });

                if (!response.ok) throw new Error('Failed to send message');
                
                const data = await response.json();
                
                // Add assistant's response
                this.messages.push({
                    id: Date.now() + 1,
                    role: 'assistant',
                    content: data.data.message.content
                });

                // Scroll to bottom
                this.$nextTick(() => {
                    const messagesContainer = document.getElementById('messages');
                    if (messagesContainer) {
                        messagesContainer.scrollTop = messagesContainer.scrollHeight;
                    }
                });
            } catch (error) {
                console.error('Chat error:', error);
                this.messages.push({
                    id: Date.now() + 1,
                    role: 'system',
                    content: 'Sorry, I encountered an error processing your message.'
                });
            } finally {
                this.loading = false;
            }
        }
    }));
});