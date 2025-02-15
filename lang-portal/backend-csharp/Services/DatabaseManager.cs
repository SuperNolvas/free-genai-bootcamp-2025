using Microsoft.EntityFrameworkCore;
using Backend.Data;

namespace Backend.Services;

public class DatabaseManager
{
    private readonly AppDbContext _context;
    private readonly DataSeeder _seeder;
    private readonly ILogger<DatabaseManager> _logger;

    public DatabaseManager(
        AppDbContext context,
        DataSeeder seeder,
        ILogger<DatabaseManager> logger)
    {
        _context = context;
        _seeder = seeder;
        _logger = logger;
    }

    public async Task InitializeDatabaseAsync()
    {
        try
        {
            _logger.LogInformation("Initializing database...");
            await _context.Database.EnsureCreatedAsync();
            _logger.LogInformation("Database initialized successfully.");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "An error occurred while initializing the database.");
            throw;
        }
    }

    public async Task MigrateDatabaseAsync()
    {
        try
        {
            _logger.LogInformation("Running database migrations...");
            await _context.Database.MigrateAsync();
            _logger.LogInformation("Database migrations completed successfully.");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "An error occurred while running database migrations.");
            throw;
        }
    }

    public async Task SeedDatabaseAsync()
    {
        try
        {
            _logger.LogInformation("Seeding database...");
            await _seeder.SeedDataAsync();
            _logger.LogInformation("Database seeded successfully.");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "An error occurred while seeding the database.");
            throw;
        }
    }

    public async Task ResetDatabaseAsync()
    {
        try
        {
            _logger.LogInformation("Resetting database...");
            await _context.Database.EnsureDeletedAsync();
            await InitializeDatabaseAsync();
            await MigrateDatabaseAsync();
            await SeedDatabaseAsync();
            _logger.LogInformation("Database reset completed successfully.");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "An error occurred while resetting the database.");
            throw;
        }
    }
} 