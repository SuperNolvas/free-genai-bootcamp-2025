using Microsoft.Extensions.Diagnostics.HealthChecks;
using Backend.Data;
using Microsoft.EntityFrameworkCore;

namespace Backend.Services;

public class DatabaseHealthCheck : IHealthCheck
{
    private readonly AppDbContext _context;
    private readonly ILogger<DatabaseHealthCheck> _logger;

    public DatabaseHealthCheck(AppDbContext context, ILogger<DatabaseHealthCheck> logger)
    {
        _context = context;
        _logger = logger;
    }

    public async Task<HealthCheckResult> CheckHealthAsync(HealthCheckContext context, CancellationToken cancellationToken = default)
    {
        try
        {
            // Test database connection
            await _context.Database.CanConnectAsync(cancellationToken);

            // Check if essential tables exist and have data
            var hasWords = await _context.Words.AnyAsync(cancellationToken);
            var hasGroups = await _context.Groups.AnyAsync(cancellationToken);

            var data = new Dictionary<string, object>
            {
                { "hasWords", hasWords },
                { "hasGroups", hasGroups }
            };

            return HealthCheckResult.Healthy("Database is healthy", data: data);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Database health check failed");
            return HealthCheckResult.Unhealthy("Database is unhealthy", ex);
        }
    }
} 