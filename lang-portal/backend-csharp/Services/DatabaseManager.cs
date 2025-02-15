using Microsoft.EntityFrameworkCore;
using Backend.Data;
using Microsoft.Extensions.Configuration;
using Backend.Models;

namespace Backend.Services;

public class DatabaseManager
{
    private readonly AppDbContext _context;
    private readonly DataSeeder _seeder;
    private readonly ILogger<DatabaseManager> _logger;
    private readonly IConfiguration _configuration;

    public DatabaseManager(
        AppDbContext context,
        DataSeeder seeder,
        ILogger<DatabaseManager> logger,
        IConfiguration configuration)
    {
        _context = context;
        _seeder = seeder;
        _logger = logger;
        _configuration = configuration;
    }

    public async Task InitializeDatabaseAsync()
    {
        try
        {
            _logger.LogInformation("Initializing database...");
            
            var dbPath = _configuration.GetConnectionString("DefaultConnection");
            if (string.IsNullOrEmpty(dbPath))
            {
                throw new InvalidOperationException("Database connection string is not configured");
            }

            var directory = Path.GetDirectoryName(dbPath.Replace("Data Source=", ""));
            if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
            {
                _logger.LogInformation("Creating database directory: {Directory}", directory);
                Directory.CreateDirectory(directory);
            }

            await _context.Database.EnsureCreatedAsync();
            _logger.LogInformation("Database initialized successfully");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error initializing database");
            throw;
        }
    }

    public async Task MigrateDatabaseAsync()
    {
        try
        {
            _logger.LogInformation("Applying database migrations...");
            await _context.Database.MigrateAsync();
            _logger.LogInformation("Database migrations applied successfully");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error applying database migrations");
            throw;
        }
    }

    public async Task SeedDatabaseAsync()
    {
        try
        {
            _logger.LogInformation("Seeding database...");
            await _seeder.SeedDataAsync();
            _logger.LogInformation("Database seeded successfully");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error seeding database");
            throw;
        }
    }

    public async Task ResetDatabaseAsync()
    {
        try
        {
            _logger.LogInformation("Resetting database...");
            
            // Delete all word reviews
            await _context.WordReviewItems.Where(_ => true).ExecuteDeleteAsync();
            
            // Delete all study sessions
            await _context.StudySessions.Where(_ => true).ExecuteDeleteAsync();
            
            // Delete all study activities
            await _context.StudyActivities.Where(_ => true).ExecuteDeleteAsync();

            await _context.SaveChangesAsync();
            _logger.LogInformation("Database reset successfully");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error resetting database");
            throw;
        }
    }

    public async Task<bool> VerifyDatabaseIntegrityAsync()
    {
        try
        {
            _logger.LogInformation("Verifying database integrity...");

            // Check if essential tables exist and have proper relationships
            var hasWords = await _context.Words.AnyAsync();
            var hasGroups = await _context.Groups.AnyAsync();
            var hasWordGroups = await _context.Set<WordGroup>().AnyAsync();

            if (!hasWords || !hasGroups)
            {
                _logger.LogWarning("Database integrity check failed: Missing essential data");
                return false;
            }

            _logger.LogInformation("Database integrity verified successfully");
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error verifying database integrity");
            throw;
        }
    }
} 