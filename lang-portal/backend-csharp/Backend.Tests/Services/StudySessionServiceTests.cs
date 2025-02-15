using System;
using System.Threading.Tasks;
using Xunit;
using Moq;
using Backend.Services;
using Backend.Services.Repositories;
using Backend.Models;
using Microsoft.Extensions.Logging;

namespace Backend.Tests.Services;

public class StudySessionServiceTests
{
    private readonly Mock<IStudySessionRepository> _mockSessionRepo;
    private readonly Mock<IWordReviewRepository> _mockReviewRepo;
    private readonly Mock<ILogger<StudySessionService>> _mockLogger;
    private readonly StudySessionService _service;

    public StudySessionServiceTests()
    {
        _mockSessionRepo = new Mock<IStudySessionRepository>();
        _mockReviewRepo = new Mock<IWordReviewRepository>();
        _mockLogger = new Mock<ILogger<StudySessionService>>();
        _service = new StudySessionService(
            _mockSessionRepo.Object,
            _mockReviewRepo.Object,
            _mockLogger.Object);
    }

    [Fact]
    public async Task GetLatestSessionAsync_ReturnsLatestSession()
    {
        // Arrange
        var session = new StudySession
        {
            Id = 1,
            GroupId = 1,
            CreatedAt = DateTime.UtcNow
        };
        _mockSessionRepo.Setup(repo => repo.GetLatestSessionAsync())
            .ReturnsAsync(session);

        // Act
        var result = await _service.GetLatestSessionAsync();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(1, result.Id);
    }

    [Fact]
    public async Task GetStudyStreakDaysAsync_ReturnsCorrectStreak()
    {
        // Arrange
        var expectedStreak = 5;
        _mockSessionRepo.Setup(repo => repo.GetStudyStreakDaysAsync())
            .ReturnsAsync(expectedStreak);

        // Act
        var result = await _service.GetStudyStreakDaysAsync();

        // Assert
        Assert.Equal(expectedStreak, result);
    }

    [Fact]
    public async Task AddWordReviewAsync_AddsReview()
    {
        // Arrange
        var sessionId = 1;
        var wordId = 1;
        var correct = true;

        // Act
        await _service.AddWordReviewAsync(sessionId, wordId, correct);

        // Assert
        _mockReviewRepo.Verify(repo => repo.AddAsync(
            It.Is<WordReviewItem>(r =>
                r.StudySessionId == sessionId &&
                r.WordId == wordId &&
                r.Correct == correct)), Times.Once);
    }
} 