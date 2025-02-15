using Microsoft.AspNetCore.Mvc;
using Backend.Models;
using Backend.Services;

namespace Backend.Controllers;

[ApiController]
[Route("api/study_activities")]
public class StudyActivitiesController : ControllerBase
{
    private readonly IStudyActivityService _activityService;
    private readonly IStudySessionService _sessionService;
    private readonly ILogger<StudyActivitiesController> _logger;

    public StudyActivitiesController(
        IStudyActivityService activityService,
        IStudySessionService sessionService,
        ILogger<StudyActivitiesController> logger)
    {
        _activityService = activityService;
        _sessionService = sessionService;
        _logger = logger;
    }

    [HttpGet("{id}")]
    public async Task<IActionResult> GetActivity(int id)
    {
        try
        {
            var activity = await _activityService.GetActivityWithDetailsAsync(id);
            if (activity == null)
            {
                return NotFound(new { message = $"Study activity with ID {id} not found" });
            }

            return Ok(new
            {
                id = activity.Id,
                name = activity.StudySession.Group.Name,
                thumbnail_url = "https://example.com/thumbnail.jpg", // TODO: Implement actual thumbnail
                description = "Practice your vocabulary with flashcards" // TODO: Add description to model
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving study activity {ActivityId}", id);
            return StatusCode(500, new { message = "An error occurred while retrieving the study activity" });
        }
    }

    [HttpGet("{id}/study_sessions")]
    public async Task<IActionResult> GetActivitySessions(int id, [FromQuery] int page = 1, [FromQuery] int pageSize = 100)
    {
        try
        {
            var sessions = await _activityService.GetActivitySessionsAsync(id);
            var pagedSessions = sessions.Skip((page - 1) * pageSize).Take(pageSize);

            return Ok(new
            {
                items = pagedSessions.Select(s => new
                {
                    id = s.Id,
                    activity_name = s.StudyActivity.StudySession.Group.Name,
                    group_name = s.Group.Name,
                    start_time = s.CreatedAt,
                    end_time = s.CreatedAt.AddMinutes(10), // TODO: Implement actual end time
                    review_items_count = s.ReviewItems.Count
                }),
                pagination = new
                {
                    current_page = page,
                    total_pages = (int)Math.Ceiling(sessions.Count() / (double)pageSize),
                    total_items = sessions.Count(),
                    items_per_page = pageSize
                }
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving sessions for activity {ActivityId}", id);
            return StatusCode(500, new { message = "An error occurred while retrieving activity sessions" });
        }
    }

    [HttpPost]
    public async Task<IActionResult> CreateActivity([FromBody] StudyActivity activity)
    {
        try
        {
            var createdActivity = await _activityService.CreateActivityAsync(activity);
            var session = await _sessionService.CreateSessionAsync(activity.GroupId, createdActivity.Id);

            return Ok(new { id = createdActivity.Id, group_id = activity.GroupId });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating study activity");
            return StatusCode(500, new { message = "An error occurred while creating the study activity" });
        }
    }
} 