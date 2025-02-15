using Backend.Models;

namespace Backend.Services;

public interface IStudyActivityService
{
    Task<StudyActivity?> GetActivityAsync(int id);
    Task<IEnumerable<StudyActivity>> GetAllActivitiesAsync(int page = 1, int pageSize = 100);
    Task<StudyActivity?> GetActivityWithDetailsAsync(int id);
    Task<IEnumerable<StudyActivity>> GetActivitiesByGroupAsync(int groupId);
    Task<StudyActivity> CreateActivityAsync(StudyActivity activity);
    Task UpdateActivityAsync(StudyActivity activity);
    Task DeleteActivityAsync(int id);
    Task<IEnumerable<StudySession>> GetActivitySessionsAsync(int activityId);
} 