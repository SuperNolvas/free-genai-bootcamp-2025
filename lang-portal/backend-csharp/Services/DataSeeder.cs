using System.Text.Json;
using Backend.Data;
using Backend.Models;

namespace Backend.Services;

public class DataSeeder
{
    private readonly AppDbContext _context;
    private readonly ILogger<DataSeeder> _logger;

    public DataSeeder(AppDbContext context, ILogger<DataSeeder> logger)
    {
        _context = context;
        _logger = logger;
    }

    public async Task SeedDataAsync()
    {
        try
        {
            // Ensure database is created
            await _context.Database.EnsureCreatedAsync();

            // Seed in order of dependencies
            await SeedGroupsAsync();
            await SeedWordsAsync();
            await SeedStudyActivitiesAsync();

            await _context.SaveChangesAsync();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "An error occurred while seeding the database.");
            throw;
        }
    }

    private async Task SeedGroupsAsync()
    {
        if (!_context.Groups.Any())
        {
            var groupsJson = await File.ReadAllTextAsync("Data/SeedData/groups.json");
            var groups = JsonSerializer.Deserialize<List<Group>>(groupsJson);

            if (groups != null)
            {
                await _context.Groups.AddRangeAsync(groups);
            }
        }
    }

    private async Task SeedWordsAsync()
    {
        if (!_context.Words.Any())
        {
            var wordsJson = await File.ReadAllTextAsync("Data/SeedData/basic_words.json");
            var words = JsonSerializer.Deserialize<List<Word>>(wordsJson);

            if (words != null)
            {
                await _context.Words.AddRangeAsync(words);
            }
        }
    }

    private async Task SeedStudyActivitiesAsync()
    {
        if (!_context.StudyActivities.Any())
        {
            var activitiesJson = await File.ReadAllTextAsync("Data/SeedData/study_activities.json");
            var activities = JsonSerializer.Deserialize<List<StudyActivity>>(activitiesJson);

            if (activities != null)
            {
                await _context.StudyActivities.AddRangeAsync(activities);
            }
        }
    }
} 