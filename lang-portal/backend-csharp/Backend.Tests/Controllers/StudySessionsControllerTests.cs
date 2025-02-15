using System.Net;
using System.Net.Http.Json;
using Backend.Models;
using Backend.Tests.Helpers;
using Xunit;

namespace Backend.Tests.Controllers;

public class StudySessionsControllerTests : IClassFixture<TestWebApplicationFactory>
{
    private readonly HttpClient _client;

    public StudySessionsControllerTests(TestWebApplicationFactory factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task GetSessions_ReturnsSuccessStatusCode()
    {
        // Act
        var response = await _client.GetAsync("/api/study_sessions");

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    [Fact]
    public async Task GetSessions_ReturnsPaginatedResponse()
    {
        // Act
        var response = await _client.GetAsync("/api/study_sessions?page=1&pageSize=10");
        var content = await response.Content.ReadFromJsonAsync<dynamic>();

        // Assert
        Assert.NotNull(content);
        Assert.NotNull(content.items);
        Assert.NotNull(content.pagination);
    }

    [Fact]
    public async Task ReviewWord_ValidData_ReturnsSuccess()
    {
        // Arrange
        var word = new Word
        {
            Russian = "время",
            English = "time",
            Transliteration = "vremya"
        };
        var createWordResponse = await _client.PostAsJsonAsync("/api/words", word);
        var wordId = createWordResponse.GetResourceIdFromLocation();

        var group = new Group { Name = "Time Words" };
        var createGroupResponse = await _client.PostAsJsonAsync("/api/groups", group);
        var groupId = createGroupResponse.GetResourceIdFromLocation();

        var activity = new StudyActivity { GroupId = groupId };
        var createActivityResponse = await _client.PostAsJsonAsync("/api/study_activities", activity);
        var sessionId = 1; // First session

        // Act
        var response = await _client.PostAsJsonAsync(
            $"/api/study_sessions/{sessionId}/words/{wordId}/review",
            new { correct = true });

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var content = await response.Content.ReadFromJsonAsync<dynamic>();
        Assert.True((bool)content.success);
    }

    [Fact]
    public async Task GetSessionWords_ReturnsWords()
    {
        // Arrange
        var sessionId = 1; // Use first session

        // Act
        var response = await _client.GetAsync($"/api/study_sessions/{sessionId}/words");
        var content = await response.Content.ReadFromJsonAsync<dynamic>();

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.NotNull(content.items);
    }
} 