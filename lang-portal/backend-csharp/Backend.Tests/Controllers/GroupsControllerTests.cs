using System.Net;
using System.Net.Http.Json;
using Xunit;
using Backend.Models;
using Backend.Tests.Helpers;
using Microsoft.AspNetCore.Mvc.Testing;

namespace Backend.Tests.Controllers;

public class GroupsControllerTests : IClassFixture<TestWebApplicationFactory>
{
    private readonly HttpClient _client;

    public GroupsControllerTests(TestWebApplicationFactory factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task GetGroups_ReturnsSuccessStatusCode()
    {
        // Act
        var response = await _client.GetAsync("/api/groups");

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    [Fact]
    public async Task GetGroups_ReturnsPaginatedResponse()
    {
        // Act
        var response = await _client.GetAsync("/api/groups?page=1&pageSize=10");
        var content = await response.Content.ReadFromJsonAsync<dynamic>();

        // Assert
        Assert.NotNull(content);
        Assert.NotNull(content.items);
        Assert.NotNull(content.pagination);
    }

    [Fact]
    public async Task GetGroupWords_ReturnsWords()
    {
        // Arrange
        var word = new Word
        {
            Russian = "мир",
            English = "world",
            Transliteration = "mir"
        };
        var createWordResponse = await _client.PostAsJsonAsync("/api/words", word);
        var wordId = createWordResponse.GetResourceIdFromLocation();

        var group = new Group { Name = "Basic Words" };
        var createGroupResponse = await _client.PostAsJsonAsync("/api/groups", group);
        var groupId = createGroupResponse.GetResourceIdFromLocation();

        // Act
        var response = await _client.GetAsync($"/api/groups/{groupId}/words");
        var content = await response.Content.ReadFromJsonAsync<dynamic>();

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.NotNull(content.items);
    }

    [Fact]
    public async Task GetGroupStudySessions_ReturnsStudySessions()
    {
        // Arrange
        var group = new Group { Name = "Study Group" };
        var createResponse = await _client.PostAsJsonAsync("/api/groups", group);
        var groupId = createResponse.GetResourceIdFromLocation();

        // Act
        var response = await _client.GetAsync($"/api/groups/{groupId}/study_sessions");
        var content = await response.Content.ReadFromJsonAsync<dynamic>();

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.NotNull(content.items);
    }
} 