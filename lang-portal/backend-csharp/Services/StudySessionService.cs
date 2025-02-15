using Backend.Models;
using Backend.Services.Repositories;

namespace Backend.Services;

public class StudySessionService : IStudySessionService
{
    private readonly IStudySessionRepository _sessionRepository;
    private readonly IWordReviewRepository _reviewRepository;
    private readonly ILogger<StudySessionService> _logger;

    public StudySessionService(
        IStudySessionRepository sessionRepository,
        IWordReviewRepository reviewRepository,
        ILogger<StudySessionService> logger)
    {
        _sessionRepository = sessionRepository;
        _reviewRepository = reviewRepository;
        _logger = logger;
    }

    public async Task<StudySession?> GetSessionAsync(int id)
    {
        try
        {
            return await _sessionRepository.GetByIdAsync(id);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving study session with ID {Id}", id);
            throw;
        }
    }

    public async Task<IEnumerable<StudySession>> GetAllSessionsAsync(int page = 1, int pageSize = 100)
    {
        try
        {
            var sessions = await _sessionRepository.GetAllAsync();
            return sessions
                .OrderByDescending(s => s.CreatedAt)
                .Skip((page - 1) * pageSize)
                .Take(pageSize);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving study sessions for page {Page}", page);
            throw;
        }
    }

    public async Task<StudySession?> GetLatestSessionAsync()
    {
        try
        {
            return await _sessionRepository.GetLatestSessionAsync();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving latest study session");
            throw;
        }
    }

    public async Task<StudySession> CreateSessionAsync(int groupId, int studyActivityId)
    {
        try
        {
            var session = new StudySession
            {
                GroupId = groupId,
                StudyActivityId = studyActivityId,
                CreatedAt = DateTime.UtcNow
            };

            return await _sessionRepository.AddAsync(session);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating study session for group {GroupId}", groupId);
            throw;
        }
    }

    public async Task<IEnumerable<WordReviewItem>> GetSessionReviewsAsync(int sessionId)
    {
        try
        {
            return await _reviewRepository.GetReviewsBySessionAsync(sessionId);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving reviews for session {SessionId}", sessionId);
            throw;
        }
    }

    public async Task<int> GetStudyStreakDaysAsync()
    {
        try
        {
            return await _sessionRepository.GetStudyStreakDaysAsync();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error calculating study streak days");
            throw;
        }
    }

    public async Task<int> GetTotalStudySessionsAsync()
    {
        try
        {
            var sessions = await _sessionRepository.GetAllAsync();
            return sessions.Count();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting total study sessions count");
            throw;
        }
    }

    public async Task AddWordReviewAsync(int sessionId, int wordId, bool correct)
    {
        try
        {
            var review = new WordReviewItem
            {
                StudySessionId = sessionId,
                WordId = wordId,
                Correct = correct,
                CreatedAt = DateTime.UtcNow
            };

            await _reviewRepository.AddAsync(review);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error adding word review for session {SessionId}, word {WordId}", sessionId, wordId);
            throw;
        }
    }
} 