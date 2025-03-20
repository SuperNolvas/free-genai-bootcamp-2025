export class WebSocketService {
    private ws: WebSocket | null = null;
    private messageHandlers: ((data: any) => void)[] = [];
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000;

    constructor(private endpoint: string) {
        this.connect();
    }

    private async connect() {
        try {
            // Get authentication token from localStorage or your auth service
            const token = localStorage.getItem('token');
            if (!token) {
                throw new Error('No authentication token available');
            }

            // Create WebSocket connection with auth token
            const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}${this.endpoint}`;
            this.ws = new WebSocket(`${wsUrl}?token=${token}`);

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.messageHandlers.forEach(handler => handler(data));
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            this.ws.onclose = () => {
                this.handleDisconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.handleDisconnect();
            };

            // Reset reconnect attempts on successful connection
            this.reconnectAttempts = 0;

        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.handleDisconnect();
        }
    }

    private handleDisconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            console.log(`Attempting to reconnect in ${delay}ms...`);
            setTimeout(() => this.connect(), delay);
        }
    }

    public send(data: any): void {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.error('WebSocket is not connected');
        }
    }

    public onMessage(handler: (data: any) => void): void {
        this.messageHandlers.push(handler);
    }

    public close(): void {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}