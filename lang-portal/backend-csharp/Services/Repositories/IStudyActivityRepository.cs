using Backend.Models;

namespace Backend.Services.Repositories;

public interface IStudyActivityRepository : IRepository<StudyActivity>
{
    Task<IEnumerable<StudyActivity>> GetActivitiesByGroupAsync(int groupId);
    Task<StudyActivity?> GetActivityWithDetailsAsync(int id);
} 