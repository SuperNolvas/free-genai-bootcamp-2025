using Microsoft.AspNetCore.Mvc;
using Backend.Models;
using Backend.Services;

namespace Backend.Controllers;

[ApiController]
[Route("api/[controller]")]
public class GroupsController : ControllerBase
{
    private readonly IGroupService _groupService;
    private readonly IWordService _wordService;
    private readonly ILogger<GroupsController> _logger;

    public GroupsController(
        IGroupService groupService,
        IWordService wordService,
        ILogger<GroupsController> logger)
    {
        _groupService = groupService;
        _wordService = wordService;
        _logger = logger;
    }

    [HttpGet]
    public async Task<IActionResult> GetGroups([FromQuery] int page = 1, [FromQuery] int pageSize = 100)
    {
        try
        {
            var groups = await _groupService.GetAllGroupsAsync(page, pageSize);
            var totalGroups = await _groupService.GetTotalActiveGroupsAsync();

            return Ok(new
            {
                items = groups.Select(g => new
                {
                    id = g.GroupsId,
                    name = g.Name,
                    word_count = g.WordGroups.Count
                }),
                pagination = new
                {
                    current_page = page,
                    total_pages = (int)Math.Ceiling(totalGroups / (double)pageSize),
                    total_items = totalGroups,
                    items_per_page = pageSize
                }
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving groups");
            return StatusCode(500, new { message = "An error occurred while retrieving groups" });
        }
    }

    [HttpGet("{id}")]
    public async Task<IActionResult> GetGroup(int id)
    {
        try
        {
            var group = await _groupService.GetGroupWithWordsAsync(id);
            if (group == null)
            {
                return NotFound(new { message = $"Group with ID {id} not found" });
            }

            return Ok(new
            {
                id = group.GroupsId,
                name = group.Name,
                stats = new
                {
                    total_word_count = group.WordGroups.Count
                }
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving group {GroupId}", id);
            return StatusCode(500, new { message = "An error occurred while retrieving the group" });
        }
    }

    [HttpGet("{id}/words")]
    public async Task<IActionResult> GetGroupWords(int id, [FromQuery] int page = 1, [FromQuery] int pageSize = 100)
    {
        try
        {
            var words = await _wordService.GetWordsByGroupAsync(id);
            var pagedWords = words.Skip((page - 1) * pageSize).Take(pageSize);

            return Ok(new
            {
                items = pagedWords.Select(w => new
                {
                    russian = w.Russian,
                    transliteration = w.Transliteration,
                    english = w.English,
                    correct_count = w.ReviewItems.Count(r => r.Correct),
                    wrong_count = w.ReviewItems.Count(r => !r.Correct)
                }),
                pagination = new
                {
                    current_page = page,
                    total_pages = (int)Math.Ceiling(words.Count() / (double)pageSize),
                    total_items = words.Count(),
                    items_per_page = pageSize
                }
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving words for group {GroupId}", id);
            return StatusCode(500, new { message = "An error occurred while retrieving group words" });
        }
    }

    [HttpGet("{id}/study_sessions")]
    public async Task<IActionResult> GetGroupStudySessions(int id)
    {
        try
        {
            var sessions = await _groupService.GetGroupStudySessionsAsync(id);
            return Ok(new
            {
                items = sessions.Select(s => new
                {
                    id = s.Id,
                    activity_name = s.StudyActivity.StudySession.Group.Name,
                    group_name = s.Group.Name,
                    start_time = s.CreatedAt,
                    review_items_count = s.ReviewItems.Count
                })
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving study sessions for group {GroupId}", id);
            return StatusCode(500, new { message = "An error occurred while retrieving group study sessions" });
        }
    }
} 