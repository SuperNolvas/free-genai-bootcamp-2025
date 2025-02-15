using Microsoft.AspNetCore.Mvc;
using Backend.Services;

namespace Backend.Controllers;

[ApiController]
[Route("api/[controller]")]
public class DashboardController : ControllerBase
{
    private readonly IWordService _wordService;
    private readonly IStudySessionService _sessionService;
    private readonly IGroupService _groupService;
    private readonly ILogger<DashboardController> _logger;

    public DashboardController(
        IWordService wordService,
        IStudySessionService sessionService,
        IGroupService groupService,
        ILogger<DashboardController> logger)
    {
        _wordService = wordService;
        _sessionService = sessionService;
        _groupService = groupService;
        _logger = logger;
    }

    [HttpGet("last_study_session")]
    public async Task<IActionResult> GetLastStudySession()
    {
        try
        {
            var session = await _sessionService.GetLatestSessionAsync();
            if (session == null)
            {
                return NotFound(new { message = "No study sessions found" });
            }

            return Ok(new
            {
                id = session.Id,
                group_id = session.GroupId,
                created_at = session.CreatedAt,
                study_activity_id = session.StudyActivityId,
                group_name = session.Group.Name
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving last study session");
            return StatusCode(500, new { message = "An error occurred while retrieving the last study session" });
        }
    }

    [HttpGet("study_progress")]
    public async Task<IActionResult> GetStudyProgress()
    {
        try
        {
            var (totalStudied, totalAvailable) = await _wordService.GetStudyProgressAsync();

            return Ok(new
            {
                total_words_studied = totalStudied,
                total_available_words = totalAvailable
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving study progress");
            return StatusCode(500, new { message = "An error occurred while retrieving study progress" });
        }
    }

    [HttpGet("quick-stats")]
    public async Task<IActionResult> GetQuickStats()
    {
        try
        {
            var totalSessions = await _sessionService.GetTotalStudySessionsAsync();
            var activeGroups = await _groupService.GetTotalActiveGroupsAsync();
            var streakDays = await _sessionService.GetStudyStreakDaysAsync();

            return Ok(new
            {
                total_study_sessions = totalSessions,
                total_active_groups = activeGroups,
                study_streak_days = streakDays
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving quick stats");
            return StatusCode(500, new { message = "An error occurred while retrieving quick stats" });
        }
    }
} 