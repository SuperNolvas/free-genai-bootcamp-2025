using Backend.Data;
using Backend.Models;
using Backend.Tests.Helpers;
using Microsoft.EntityFrameworkCore;
using Xunit;

namespace Backend.Tests.Data;

public class DatabaseTests
{
    [Fact]
    public async Task CanAddAndRetrieveWord()
    {
        // Arrange
        using var context = TestDbContextFactory.Create();
        var word = new Word
        {
            Russian = "вода",
            English = "water",
            Transliteration = "voda"
        };

        // Act
        context.Words.Add(word);
        await context.SaveChangesAsync();

        var retrievedWord = await context.Words
            .FirstOrDefaultAsync(w => w.Russian == "вода");

        // Assert
        Assert.NotNull(retrievedWord);
        Assert.Equal("water", retrievedWord.English);
    }

    [Fact]
    public async Task CanCreateWordGroup()
    {
        // Arrange
        using var context = TestDbContextFactory.Create();
        var word = new Word
        {
            Russian = "собака",
            English = "dog",
            Transliteration = "sobaka"
        };
        var group = new Group { Name = "Animals" };

        // Act
        context.Words.Add(word);
        context.Groups.Add(group);
        await context.SaveChangesAsync();

        var wordGroup = new WordGroup
        {
            WordId = word.WordsId,
            GroupId = group.GroupsId
        };
        context.Set<WordGroup>().Add(wordGroup);
        await context.SaveChangesAsync();

        var retrievedGroup = await context.Groups
            .Include(g => g.WordGroups)
            .ThenInclude(wg => wg.Word)
            .FirstOrDefaultAsync(g => g.Name == "Animals");

        // Assert
        Assert.NotNull(retrievedGroup);
        Assert.Single(retrievedGroup.WordGroups);
        Assert.Equal("собака", retrievedGroup.WordGroups.First().Word.Russian);
    }
} 