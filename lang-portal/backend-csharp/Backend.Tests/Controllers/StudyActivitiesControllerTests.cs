using System.Net;
using System.Net.Http.Json;
using Xunit;
using Backend.Models;
using Backend.Tests.Helpers;
using Microsoft.AspNetCore.Mvc.Testing;

namespace Backend.Tests.Controllers;

public class StudyActivitiesControllerTests : IClassFixture<TestWebApplicationFactory>
{
    private readonly HttpClient _client;

    public StudyActivitiesControllerTests(TestWebApplicationFactory factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task GetActivity_ReturnsSuccessStatusCode()
    {
        // Arrange
        var group = new Group { Name = "Activity Group" };
        var createGroupResponse = await _client.PostAsJsonAsync("/api/groups", group);
        var groupId = createGroupResponse.GetResourceIdFromLocation();

        var activity = new StudyActivity { GroupId = groupId };
        var createResponse = await _client.PostAsJsonAsync("/api/study_activities", activity);
        var activityId = createResponse.GetResourceIdFromLocation();

        // Act
        var response = await _client.GetAsync($"/api/study_activities/{activityId}");

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    [Fact]
    public async Task GetActivitySessions_ReturnsPaginatedResponse()
    {
        // Arrange
        var group = new Group { Name = "Activity Group" };
        var createGroupResponse = await _client.PostAsJsonAsync("/api/groups", group);
        var groupId = createGroupResponse.GetResourceIdFromLocation();

        var activity = new StudyActivity { GroupId = groupId };
        var createResponse = await _client.PostAsJsonAsync("/api/study_activities", activity);
        var activityId = createResponse.GetResourceIdFromLocation();

        // Act
        var response = await _client.GetAsync($"/api/study_activities/{activityId}/study_sessions?page=1&pageSize=10");
        var content = await response.Content.ReadFromJsonAsync<dynamic>();

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.NotNull(content.items);
        Assert.NotNull(content.pagination);
    }

    [Fact]
    public async Task CreateActivity_ValidData_ReturnsSuccess()
    {
        // Arrange
        var group = new Group { Name = "New Activity Group" };
        var createGroupResponse = await _client.PostAsJsonAsync("/api/groups", group);
        var groupId = createGroupResponse.GetResourceIdFromLocation();

        var activity = new StudyActivity { GroupId = groupId };

        // Act
        var response = await _client.PostAsJsonAsync("/api/study_activities", activity);
        var content = await response.Content.ReadFromJsonAsync<dynamic>();

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.NotNull(content.id);
        Assert.Equal(groupId, (int)content.group_id);
    }
} 