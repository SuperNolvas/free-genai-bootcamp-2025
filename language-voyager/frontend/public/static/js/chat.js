document.addEventListener('alpine:init', () => {
    Alpine.data('chat', () => ({
        messages: [],
        newMessage: '',
        currentLocation: null,
        locationContext: null,
        loading: false,

        init() {
            console.log('Chat component initialized');
            window.addEventListener('location:updated', this.handleLocationUpdate.bind(this));
        },

        destroy() {
            window.removeEventListener('location:updated', this.handleLocationUpdate.bind(this));
        },

        handleLocationUpdate(event) {
            const location = event.detail;
            console.log('Chat handling location update:', location);
            
            this.currentLocation = location.local_name || location.name;
            this.locationContext = {
                name: location.name,
                local_name: location.local_name,
                type: location.type || 'area',
                coordinates: {
                    lat: location.latitude,
                    lng: location.longitude
                }
            };
        },

        async sendMessage() {
            if (!this.newMessage.trim() || this.loading) return;
            
            const token = localStorage.getItem('token');
            const userMessage = this.newMessage.trim();
            const timestamp = new Date().toISOString();
            
            // Add user message
            const userMsg = {
                id: Date.now(),
                role: 'user',
                content: userMessage,
                timestamp: timestamp
            };
            
            this.messages.push(userMsg);
            this.newMessage = '';
            this.loading = true;

            try {
                // Construct request payload according to server schema
                const payload = {
                    messages: [userMsg],
                    context: {
                        poi_type: this.locationContext?.type || 'area',
                        formality_level: 'polite',
                        dialect: 'standard',
                        difficulty_level: 50,
                        region_specific_customs: {},
                        current_location: {
                            name: this.locationContext?.name,
                            local_name: this.locationContext?.local_name,
                            type: this.locationContext?.type || 'area',
                            coordinates: this.locationContext?.coordinates
                        }
                    }
                };

                console.log('Sending chat request:', JSON.stringify(payload, null, 2));

                const response = await fetch('/api/v1/conversation/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    throw new Error(`Server error: ${response.statusText}`);
                }

                const responseData = await response.json();
                console.log('Server response:', responseData);

                if (!responseData.success) {
                    throw new Error(responseData.message);
                }

                // Add assistant's response using the new response format
                if (responseData.data && responseData.data.message) {
                    this.messages.push({
                        id: Date.now() + 1,
                        role: responseData.data.message.role,
                        content: responseData.data.message.content,
                        timestamp: responseData.data.message.timestamp || new Date().toISOString()
                    });
                } else {
                    throw new Error('Invalid response format from server');
                }

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
                    content: `Error: ${error.message}`,
                    timestamp: new Date().toISOString()
                });
            } finally {
                this.loading = false;
            }
        }
    }));
});