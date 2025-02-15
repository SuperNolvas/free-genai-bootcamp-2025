using System.Net;
using System.Net.Http.Json;
using Xunit;
using Microsoft.AspNetCore.Mvc.Testing;

namespace Backend.Tests.Controllers;

public class DashboardControllerTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;

    public DashboardControllerTests(WebApplicationFactory<Program> factory)
    {
        _factory = factory;
    }

    [Fact]
    public async Task GetLastStudySession_ReturnsSuccessStatusCode()
    {
        // Arrange
        var client = _factory.CreateClient();

        // Act
        var response = await client.GetAsync("/api/dashboard/last_study_session");

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    [Fact]
    public async Task GetStudyProgress_ReturnsProgressData()
    {
        // Arrange
        var client = _factory.CreateClient();

        // Act
        var response = await client.GetAsync("/api/dashboard/study_progress");
        var content = await response.Content.ReadFromJsonAsync<dynamic>();

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.NotNull(content.total_words_studied);
        Assert.NotNull(content.total_available_words);
    }

    [Fact]
    public async Task GetQuickStats_ReturnsStats()
    {
        // Act
        var response = await _factory.CreateClient().GetAsync("/api/dashboard/quick-stats");
        var content = await response.Content.ReadFromJsonAsync<dynamic>();

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.NotNull(content.total_study_sessions);
        Assert.NotNull(content.total_active_groups);
        Assert.NotNull(content.study_streak_days);
    }
} 