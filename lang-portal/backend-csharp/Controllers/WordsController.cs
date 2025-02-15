using Microsoft.AspNetCore.Mvc;
using Backend.Models;
using Backend.Services;

namespace Backend.Controllers;

[ApiController]
[Route("api/[controller]")]
public class WordsController : ControllerBase
{
    private readonly IWordService _wordService;
    private readonly ILogger<WordsController> _logger;

    public WordsController(IWordService wordService, ILogger<WordsController> logger)
    {
        _wordService = wordService;
        _logger = logger;
    }

    [HttpGet]
    public async Task<IActionResult> GetWords([FromQuery] int page = 1, [FromQuery] int pageSize = 100)
    {
        try
        {
            var words = await _wordService.GetAllWordsAsync(page, pageSize);
            var totalWords = await _wordService.GetStudyProgressAsync();

            return Ok(new
            {
                items = words.Select(w => new
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
                    total_pages = (int)Math.Ceiling(totalWords.totalAvailable / (double)pageSize),
                    total_items = totalWords.totalAvailable,
                    items_per_page = pageSize
                }
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving words");
            return StatusCode(500, new { message = "An error occurred while retrieving words" });
        }
    }

    [HttpGet("{id}")]
    public async Task<IActionResult> GetWord(int id)
    {
        try
        {
            var word = await _wordService.GetWordAsync(id);
            if (word == null)
            {
                return NotFound(new { message = $"Word with ID {id} not found" });
            }

            return Ok(new
            {
                russian = word.Russian,
                transliteration = word.Transliteration,
                english = word.English,
                stats = new
                {
                    correct_count = word.ReviewItems.Count(r => r.Correct),
                    wrong_count = word.ReviewItems.Count(r => !r.Correct)
                },
                groups = word.WordGroups.Select(wg => new
                {
                    id = wg.GroupId,
                    name = wg.Group.Name
                })
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving word {WordId}", id);
            return StatusCode(500, new { message = "An error occurred while retrieving the word" });
        }
    }

    [HttpPost]
    public async Task<IActionResult> CreateWord([FromBody] Word word)
    {
        try
        {
            var createdWord = await _wordService.AddWordAsync(word);
            return CreatedAtAction(nameof(GetWord), new { id = createdWord.WordsId }, createdWord);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating word");
            return StatusCode(500, new { message = "An error occurred while creating the word" });
        }
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> UpdateWord(int id, [FromBody] Word word)
    {
        try
        {
            if (id != word.WordsId)
            {
                return BadRequest(new { message = "ID mismatch" });
            }

            await _wordService.UpdateWordAsync(word);
            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating word {WordId}", id);
            return StatusCode(500, new { message = "An error occurred while updating the word" });
        }
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> DeleteWord(int id)
    {
        try
        {
            await _wordService.DeleteWordAsync(id);
            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting word {WordId}", id);
            return StatusCode(500, new { message = "An error occurred while deleting the word" });
        }
    }
} 