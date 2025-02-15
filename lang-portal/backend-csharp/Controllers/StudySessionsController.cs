using Microsoft.AspNetCore.Mvc;
using Backend.Models;
using Backend.Services;

namespace Backend.Controllers;

[ApiController]
[Route("api/study_sessions")]
public class StudySessionsController : ControllerBase
{
    private readonly IStudySessionService _sessionService;
    private readonly ILogger<StudySessionsController> _logger;

    public StudySessionsController(
        IStudySessionService sessionService,
        ILogger<StudySessionsController> logger)
    {
        _sessionService = sessionService;
        _logger = logger;
    }

    [HttpGet]
    public async Task<IActionResult> GetSessions([FromQuery] int page = 1, [FromQuery] int pageSize = 100)
    {
        try
        {
            var sessions = await _sessionService.GetAllSessionsAsync(page, pageSize);
            var totalSessions = await _sessionService.GetTotalStudySessionsAsync();

            return Ok(new
            {
                items = sessions.Select(s => new
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
                    total_pages = (int)Math.Ceiling(totalSessions / (double)pageSize),
                    total_items = totalSessions,
                    items_per_page = pageSize
                }
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving study sessions");
            return StatusCode(500, new { message = "An error occurred while retrieving study sessions" });
        }
    }

    [HttpGet("{id}")]
    public async Task<IActionResult> GetSession(int id)
    {
        try
        {
            var session = await _sessionService.GetSessionAsync(id);
            if (session == null)
            {
                return NotFound(new { message = $"Study session with ID {id} not found" });
            }

            return Ok(new
            {
                id = session.Id,
                activity_name = session.StudyActivity.StudySession.Group.Name,
                group_name = session.Group.Name,
                start_time = session.CreatedAt,
                end_time = session.CreatedAt.AddMinutes(10), // TODO: Implement actual end time
                review_items_count = session.ReviewItems.Count
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving study session {SessionId}", id);
            return StatusCode(500, new { message = "An error occurred while retrieving the study session" });
        }
    }

    [HttpGet("{id}/words")]
    public async Task<IActionResult> GetSessionWords(int id)
    {
        try
        {
            var reviews = await _sessionService.GetSessionReviewsAsync(id);
            return Ok(new
            {
                items = reviews.Select(r => new
                {
                    russian = r.Word.Russian,
                    transliteration = r.Word.Transliteration,
                    english = r.Word.English,
                    correct_count = r.Word.ReviewItems.Count(wr => wr.Correct),
                    wrong_count = r.Word.ReviewItems.Count(wr => !wr.Correct)
                })
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving words for session {SessionId}", id);
            return StatusCode(500, new { message = "An error occurred while retrieving session words" });
        }
    }

    [HttpPost("{id}/words/{wordId}/review")]
    public async Task<IActionResult> ReviewWord(int id, int wordId, [FromBody] ReviewRequest request)
    {
        try
        {
            await _sessionService.AddWordReviewAsync(id, wordId, request.Correct);

            return Ok(new
            {
                success = true,
                word_id = wordId,
                study_session_id = id,
                correct = request.Correct,
                created_at = DateTime.UtcNow
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error reviewing word {WordId} in session {SessionId}", wordId, id);
            return StatusCode(500, new { message = "An error occurred while reviewing the word" });
        }
    }
}

public class ReviewRequest
{
    public bool Correct { get; set; }
} 