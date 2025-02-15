using System.Net;
using System.Net.Http.Json;
using Backend.Tests.Helpers;
using Xunit;

namespace Backend.Tests.Controllers;

public class DashboardControllerTests : IClassFixture<TestWebApplicationFactory>
{
    private readonly HttpClient _client;

    public DashboardControllerTests(TestWebApplicationFactory factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task GetLastStudySession_ReturnsSuccessStatusCode()
    {
        // Act
        var response = await _client.GetAsync("/api/dashboard/last_study_session");

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    [Fact]
    public async Task GetStudyProgress_ReturnsProgressData()
    {
        // Act
        var response = await _client.GetAsync("/api/dashboard/study_progress");
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
        var response = await _client.GetAsync("/api/dashboard/quick-stats");
        var content = await response.Content.ReadFromJsonAsync<dynamic>();

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.NotNull(content.total_study_sessions);
        Assert.NotNull(content.total_active_groups);
        Assert.NotNull(content.study_streak_days);
    }
} 