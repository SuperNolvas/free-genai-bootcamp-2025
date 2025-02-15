using System.Net;
using System.Net.Http.Json;
using Xunit;
using Backend.Tests.Helpers;
using Microsoft.AspNetCore.Mvc.Testing;

namespace Backend.Tests.Controllers;

public class SystemControllerTests : IClassFixture<TestWebApplicationFactory>
{
    private readonly HttpClient _client;

    public SystemControllerTests(TestWebApplicationFactory factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task ResetHistory_ReturnsSuccess()
    {
        // Act
        var response = await _client.PostAsync("/api/reset_history", null);
        var content = await response.Content.ReadFromJsonAsync<dynamic>();

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.True((bool)content.success);
    }

    [Fact]
    public async Task FullReset_ReturnsSuccess()
    {
        // Act
        var response = await _client.PostAsync("/api/full_reset", null);
        var content = await response.Content.ReadFromJsonAsync<dynamic>();

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.True((bool)content.success);
    }
} 