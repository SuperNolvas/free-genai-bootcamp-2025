// filepath: /home/phil/free-genai-bootcamp-2025/language-voyager/frontend/src/components/ArcGISUsageAlert.tsx
import React, { useEffect, useState } from 'react';
import arcgisUsageMonitor, { ArcGISUsageStats } from '@/services/arcgis-usage';

interface ArcGISUsageAlertProps {
  showDetailedStats?: boolean;
}

const ArcGISUsageAlert: React.FC<ArcGISUsageAlertProps> = ({ showDetailedStats = false }) => {
  const [stats, setStats] = useState<ArcGISUsageStats | null>(null);
  const [alerts, setAlerts] = useState<{ operation: string; level: string; message: string }[]>([]);

  useEffect(() => {
    // Start monitoring and subscribe to updates
    arcgisUsageMonitor.startMonitoring();
    
    const unsubscribe = arcgisUsageMonitor.onUsageUpdate(newStats => {
      setStats(newStats);
      setAlerts(arcgisUsageMonitor.getCurrentAlerts());
    });
    
    // If we already have stats, set them immediately
    const currentStats = arcgisUsageMonitor.getUsageStats();
    if (currentStats) {
      setStats(currentStats);
      setAlerts(arcgisUsageMonitor.getCurrentAlerts());
    }
    
    return () => {
      unsubscribe();
      // Don't stop monitoring on unmount because other components might be using it
    };
  }, []);
  
  // If no alerts or stats, don't render anything
  if (alerts.length === 0 && (!stats || !showDetailedStats)) {
    return null;
  }

  return (
    <div className="arcgis-usage-alerts">
      {alerts.length > 0 && (
        <div className="alerts-container">
          {alerts.map((alert, index) => (
            <div 
              key={`${alert.operation}-${index}`} 
              className={`alert alert-${alert.level}`}
            >
              <span className="alert-icon">
                {alert.level === 'critical' ? '⚠️' : alert.level === 'high' ? '⚠' : 'ℹ️'}
              </span>
              <span className="alert-message">{alert.message}</span>
            </div>
          ))}
        </div>
      )}
      
      {showDetailedStats && stats && (
        <div className="usage-stats">
          <h4>ArcGIS Usage Statistics</h4>
          <div className="stat-item">
            <label>Daily Credits:</label>
            <div className="stat-bar">
              <div 
                className="stat-progress" 
                style={{ 
                  width: `${Math.min(stats.daily_credits_percentage, 100)}%`,
                  backgroundColor: getColorForPercentage(stats.daily_credits_percentage)
                }}
              />
            </div>
            <span className="stat-text">
              {stats.daily_credits_used.toFixed(2)} / {stats.daily_credits_limit} 
              ({stats.daily_credits_percentage.toFixed(1)}%)
            </span>
          </div>
          
          {Object.entries(stats.monthly_operations).map(([operation, opStats]) => (
            <div key={operation} className="stat-item">
              <label>{operation.replace(/_/g, ' ')}:</label>
              <div className="stat-bar">
                <div 
                  className="stat-progress" 
                  style={{ 
                    width: `${Math.min(opStats.percentage, 100)}%`,
                    backgroundColor: getColorForPercentage(opStats.percentage)
                  }}
                />
              </div>
              <span className="stat-text">
                {opStats.count} / {opStats.limit} 
                ({opStats.percentage.toFixed(1)}%)
              </span>
            </div>
          ))}
        </div>
      )}
      
      <style jsx>{`
        .arcgis-usage-alerts {
          margin: 10px 0;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
            Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        }
        
        .alerts-container {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }
        
        .alert {
          padding: 8px 12px;
          border-radius: 4px;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .alert-critical {
          background-color: rgba(244, 67, 54, 0.1);
          border-left: 4px solid #f44336;
          color: #d32f2f;
        }
        
        .alert-high {
          background-color: rgba(255, 152, 0, 0.1);
          border-left: 4px solid #ff9800;
          color: #ef6c00;
        }
        
        .alert-moderate {
          background-color: rgba(255, 235, 59, 0.1);
          border-left: 4px solid #ffeb3b;
          color: #f57f17;
        }
        
        .alert-icon {
          font-size: 1.2em;
        }
        
        .usage-stats {
          margin-top: 15px;
          padding: 10px;
          border: 1px solid #e0e0e0;
          border-radius: 4px;
        }
        
        .stat-item {
          margin: 10px 0;
        }
        
        .stat-item label {
          display: block;
          margin-bottom: 5px;
          font-weight: 500;
          text-transform: capitalize;
        }
        
        .stat-bar {
          height: 8px;
          background-color: #f0f0f0;
          border-radius: 4px;
          overflow: hidden;
          margin-bottom: 5px;
        }
        
        .stat-progress {
          height: 100%;
          border-radius: 4px;
          transition: width 0.3s ease;
        }
        
        .stat-text {
          font-size: 0.85em;
          color: #616161;
        }
      `}</style>
    </div>
  );
};

// Helper function to get color based on percentage
function getColorForPercentage(percentage: number): string {
  if (percentage >= 95) return '#f44336'; // Red (critical)
  if (percentage >= 90) return '#ff9800'; // Orange (high)
  if (percentage >= 80) return '#ffeb3b'; // Yellow (moderate)
  return '#4caf50'; // Green (normal)
}

export default ArcGISUsageAlert;