using Backend.Models;

namespace Backend.Services.Repositories;

public interface IStudySessionRepository : IRepository<StudySession>
{
    Task<StudySession?> GetLatestSessionAsync();
    Task<IEnumerable<StudySession>> GetSessionsByGroupAsync(int groupId);
    Task<int> GetStudyStreakDaysAsync();
} 