using Backend.Models;

namespace Backend.Services;

public interface IStudySessionService
{
    Task<StudySession?> GetSessionAsync(int id);
    Task<IEnumerable<StudySession>> GetAllSessionsAsync(int page = 1, int pageSize = 100);
    Task<StudySession?> GetLatestSessionAsync();
    Task<StudySession> CreateSessionAsync(int groupId, int studyActivityId);
    Task<IEnumerable<WordReviewItem>> GetSessionReviewsAsync(int sessionId);
    Task<int> GetStudyStreakDaysAsync();
    Task<int> GetTotalStudySessionsAsync();
    Task AddWordReviewAsync(int sessionId, int wordId, bool correct);
} 