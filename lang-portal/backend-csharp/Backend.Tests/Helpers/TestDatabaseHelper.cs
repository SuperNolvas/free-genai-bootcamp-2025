using Backend.Data;
using Backend.Models;
using Microsoft.EntityFrameworkCore;

namespace Backend.Tests.Helpers;

public static class TestDatabaseHelper
{
    public static async Task ResetDatabase(AppDbContext context)
    {
        await context.Database.EnsureDeletedAsync();
        await context.Database.EnsureCreatedAsync();
    }

    public static async Task SeedBasicTestData(AppDbContext context)
    {
        var group = new Group { Name = "Test Group" };
        context.Groups.Add(group);

        var word = new Word 
        { 
            Russian = "тест", 
            English = "test", 
            Transliteration = "test" 
        };
        context.Words.Add(word);

        await context.SaveChangesAsync();
    }
} 