using System.Net;
using System.Net.Http.Json;
using Backend.Models;
using Backend.Tests.Helpers;
using Microsoft.AspNetCore.Mvc.Testing;
using Xunit;

namespace Backend.Tests.Controllers;

public class WordsControllerTests : IClassFixture<TestWebApplicationFactory>
{
    private readonly HttpClient _client;

    public WordsControllerTests(TestWebApplicationFactory factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task GetWords_ReturnsSuccessStatusCode()
    {
        // Act
        var response = await _client.GetAsync("/api/words");

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    [Fact]
    public async Task GetWords_ReturnsPaginatedResponse()
    {
        // Act
        var response = await _client.GetAsync("/api/words?page=1&pageSize=10");
        var content = await response.Content.ReadFromJsonAsync<dynamic>();

        // Assert
        Assert.NotNull(content);
        Assert.NotNull(content.items);
        Assert.NotNull(content.pagination);
    }

    [Fact]
    public async Task CreateWord_ValidData_ReturnsCreatedResponse()
    {
        // Arrange
        var word = new Word
        {
            Russian = "книга",
            English = "book",
            Transliteration = "kniga"
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/words", word);

        // Assert
        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
        Assert.NotNull(response.Headers.Location);
    }

    [Fact]
    public async Task GetWord_ExistingId_ReturnsWord()
    {
        // Arrange
        var word = new Word
        {
            Russian = "дом",
            English = "house",
            Transliteration = "dom"
        };
        var createResponse = await _client.PostAsJsonAsync("/api/words", word);
        var wordId = createResponse.GetResourceIdFromLocation();

        // Act
        var response = await _client.GetAsync($"/api/words/{wordId}");
        var content = await response.Content.ReadFromJsonAsync<dynamic>();

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.Equal("дом", (string)content.russian);
        Assert.Equal("house", (string)content.english);
    }
} 