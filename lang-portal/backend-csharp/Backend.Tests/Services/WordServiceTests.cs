using Xunit;
using Moq;
using Backend.Services;
using Backend.Services.Repositories;
using Backend.Models;
using Microsoft.Extensions.Logging;

namespace Backend.Tests.Services;

public class WordServiceTests
{
    private readonly Mock<IWordRepository> _mockWordRepo;
    private readonly Mock<ILogger<WordService>> _mockLogger;
    private readonly WordService _service;

    public WordServiceTests()
    {
        _mockWordRepo = new Mock<IWordRepository>();
        _mockLogger = new Mock<ILogger<WordService>>();
        _service = new WordService(_mockWordRepo.Object, _mockLogger.Object);
    }

    [Fact]
    public async Task GetWordAsync_ExistingId_ReturnsWord()
    {
        // Arrange
        var wordId = 1;
        var word = new Word { WordsId = wordId, Russian = "привет", English = "hello" };
        _mockWordRepo.Setup(repo => repo.GetByIdAsync(wordId))
            .ReturnsAsync(word);

        // Act
        var result = await _service.GetWordAsync(wordId);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(wordId, result.WordsId);
        Assert.Equal("привет", result.Russian);
        Assert.Equal("hello", result.English);
    }

    [Fact]
    public async Task GetWordAsync_NonExistingId_ReturnsNull()
    {
        // Arrange
        var wordId = 999;
        _mockWordRepo.Setup(repo => repo.GetByIdAsync(wordId))
            .ReturnsAsync((Word)null);

        // Act
        var result = await _service.GetWordAsync(wordId);

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public async Task AddWordAsync_ValidWord_ReturnsAddedWord()
    {
        // Arrange
        var word = new Word { Russian = "спасибо", English = "thank you" };
        _mockWordRepo.Setup(repo => repo.AddAsync(It.IsAny<Word>()))
            .ReturnsAsync((Word w) => { w.WordsId = 1; return w; });

        // Act
        var result = await _service.AddWordAsync(word);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(1, result.WordsId);
        Assert.Equal("спасибо", result.Russian);
        Assert.Equal("thank you", result.English);
    }

    [Fact]
    public async Task DeleteWordAsync_ExistingId_CallsRepository()
    {
        // Arrange
        var wordId = 1;
        var word = new Word { WordsId = wordId };
        _mockWordRepo.Setup(repo => repo.GetByIdAsync(wordId))
            .ReturnsAsync(word);

        // Act
        await _service.DeleteWordAsync(wordId);

        // Assert
        _mockWordRepo.Verify(repo => repo.DeleteAsync(word), Times.Once);
    }
} 