// filepath: /home/phil/free-genai-bootcamp-2025/language-voyager/frontend/src/services/arcgis-usage.ts
import api from './api';

export interface ArcGISUsageStats {
  daily_credits_used: number;
  daily_credits_limit: number;
  daily_credits_percentage: number;
  monthly_operations: {
    [key: string]: {
      count: number;
      limit: number;
      percentage: number;
    };
  };
  alerts: {
    [key: string]: {
      level: string;
      message: string;
      timestamp: string;
    };
  };
}

interface UsageUpdateListener {
  (stats: ArcGISUsageStats): void;
}

class ArcGISUsageMonitor {
  private stats: ArcGISUsageStats | null = null;
  private listeners: UsageUpdateListener[] = [];
  private pollingInterval: number | null = null;
  private readonly POLLING_INTERVAL_MS = 60000; // Check every minute
  private readonly WARNING_THRESHOLDS = {
    MODERATE: 80,
    HIGH: 90,
    CRITICAL: 95
  };

  constructor() {
    // Initialize with empty stats
  }

  async fetchUsageStats(): Promise<ArcGISUsageStats> {
    try {
      const response = await api.get('/map/arcgis-usage');
      this.stats = response.data.data;
      this.notifyListeners();
      return this.stats;
    } catch (error) {
      console.error('Failed to fetch ArcGIS usage statistics:', error);
      throw error;
    }
  }

  startMonitoring(): void {
    // Fetch initial stats
    this.fetchUsageStats().catch(console.error);
    
    // Set up polling
    if (this.pollingInterval === null) {
      this.pollingInterval = window.setInterval(
        () => this.fetchUsageStats().catch(console.error),
        this.POLLING_INTERVAL_MS
      );
    }
  }

  stopMonitoring(): void {
    if (this.pollingInterval !== null) {
      window.clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  }

  onUsageUpdate(listener: UsageUpdateListener): () => void {
    this.listeners.push(listener);
    
    // If we already have stats, notify immediately
    if (this.stats) {
      listener(this.stats);
    }
    
    // Return unsubscribe function
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notifyListeners(): void {
    if (this.stats) {
      this.listeners.forEach(listener => listener(this.stats!));
    }
  }

  getCurrentAlerts(): { operation: string, level: string, message: string }[] {
    if (!this.stats) return [];
    
    const alerts: { operation: string, level: string, message: string }[] = [];
    
    // Check daily credits
    if (this.stats.daily_credits_percentage >= this.WARNING_THRESHOLDS.CRITICAL) {
      alerts.push({
        operation: 'daily_credits',
        level: 'critical',
        message: `Daily credits at ${this.stats.daily_credits_percentage.toFixed(1)}% of limit`
      });
    } else if (this.stats.daily_credits_percentage >= this.WARNING_THRESHOLDS.HIGH) {
      alerts.push({
        operation: 'daily_credits',
        level: 'high',
        message: `Daily credits at ${this.stats.daily_credits_percentage.toFixed(1)}% of limit`
      });
    } else if (this.stats.daily_credits_percentage >= this.WARNING_THRESHOLDS.MODERATE) {
      alerts.push({
        operation: 'daily_credits',
        level: 'moderate',
        message: `Daily credits at ${this.stats.daily_credits_percentage.toFixed(1)}% of limit`
      });
    }
    
    // Check monthly operations
    Object.entries(this.stats.monthly_operations).forEach(([operation, stats]) => {
      if (stats.percentage >= this.WARNING_THRESHOLDS.CRITICAL) {
        alerts.push({
          operation,
          level: 'critical',
          message: `${operation.replace('_', ' ')} at ${stats.percentage.toFixed(1)}% of monthly limit`
        });
      } else if (stats.percentage >= this.WARNING_THRESHOLDS.HIGH) {
        alerts.push({
          operation,
          level: 'high',
          message: `${operation.replace('_', ' ')} at ${stats.percentage.toFixed(1)}% of monthly limit`
        });
      } else if (stats.percentage >= this.WARNING_THRESHOLDS.MODERATE) {
        alerts.push({
          operation,
          level: 'moderate',
          message: `${operation.replace('_', ' ')} at ${stats.percentage.toFixed(1)}% of monthly limit`
        });
      }
    });
    
    // Add alerts from the backend
    if (this.stats.alerts) {
      Object.entries(this.stats.alerts).forEach(([operation, alert]) => {
        alerts.push({
          operation,
          level: alert.level,
          message: alert.message
        });
      });
    }
    
    return alerts;
  }

  getUsageStats(): ArcGISUsageStats | null {
    return this.stats;
  }
}

export const arcgisUsageMonitor = new ArcGISUsageMonitor();
export default arcgisUsageMonitor;