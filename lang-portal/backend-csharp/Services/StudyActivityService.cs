using Backend.Models;
using Backend.Services.Repositories;

namespace Backend.Services;

public class StudyActivityService : IStudyActivityService
{
    private readonly IStudyActivityRepository _activityRepository;
    private readonly IStudySessionRepository _sessionRepository;
    private readonly ILogger<StudyActivityService> _logger;

    public StudyActivityService(
        IStudyActivityRepository activityRepository,
        IStudySessionRepository sessionRepository,
        ILogger<StudyActivityService> logger)
    {
        _activityRepository = activityRepository;
        _sessionRepository = sessionRepository;
        _logger = logger;
    }

    public async Task<StudyActivity?> GetActivityAsync(int id)
    {
        try
        {
            return await _activityRepository.GetByIdAsync(id);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving study activity with ID {Id}", id);
            throw;
        }
    }

    public async Task<IEnumerable<StudyActivity>> GetAllActivitiesAsync(int page = 1, int pageSize = 100)
    {
        try
        {
            var activities = await _activityRepository.GetAllAsync();
            return activities
                .OrderByDescending(a => a.CreatedAt)
                .Skip((page - 1) * pageSize)
                .Take(pageSize);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving study activities for page {Page}", page);
            throw;
        }
    }

    public async Task<StudyActivity?> GetActivityWithDetailsAsync(int id)
    {
        try
        {
            return await _activityRepository.GetActivityWithDetailsAsync(id);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving study activity details for ID {Id}", id);
            throw;
        }
    }

    public async Task<IEnumerable<StudyActivity>> GetActivitiesByGroupAsync(int groupId)
    {
        try
        {
            return await _activityRepository.GetActivitiesByGroupAsync(groupId);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving activities for group {GroupId}", groupId);
            throw;
        }
    }

    public async Task<StudyActivity> CreateActivityAsync(StudyActivity activity)
    {
        try
        {
            activity.CreatedAt = DateTime.UtcNow;
            return await _activityRepository.AddAsync(activity);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating study activity for group {GroupId}", activity.GroupId);
            throw;
        }
    }

    public async Task UpdateActivityAsync(StudyActivity activity)
    {
        try
        {
            await _activityRepository.UpdateAsync(activity);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating study activity {ActivityId}", activity.Id);
            throw;
        }
    }

    public async Task DeleteActivityAsync(int id)
    {
        try
        {
            var activity = await _activityRepository.GetByIdAsync(id);
            if (activity != null)
            {
                await _activityRepository.DeleteAsync(activity);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting study activity {ActivityId}", id);
            throw;
        }
    }

    public async Task<IEnumerable<StudySession>> GetActivitySessionsAsync(int activityId)
    {
        try
        {
            var sessions = await _sessionRepository.GetAllAsync();
            return sessions.Where(s => s.StudyActivityId == activityId)
                         .OrderByDescending(s => s.CreatedAt);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving sessions for activity {ActivityId}", activityId);
            throw;
        }
    }
} 