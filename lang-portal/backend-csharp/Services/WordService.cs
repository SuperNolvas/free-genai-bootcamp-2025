using Backend.Models;
using Backend.Services.Repositories;

namespace Backend.Services;

public class WordService : IWordService
{
    private readonly IWordRepository _wordRepository;
    private readonly ILogger<WordService> _logger;

    public WordService(IWordRepository wordRepository, ILogger<WordService> logger)
    {
        _wordRepository = wordRepository;
        _logger = logger;
    }

    public async Task<Word?> GetWordAsync(int id)
    {
        try
        {
            return await _wordRepository.GetByIdAsync(id);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving word with ID {Id}", id);
            throw;
        }
    }

    public async Task<IEnumerable<Word>> GetAllWordsAsync(int page = 1, int pageSize = 100)
    {
        try
        {
            var words = await _wordRepository.GetAllAsync();
            return words.Skip((page - 1) * pageSize).Take(pageSize);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving words for page {Page}", page);
            throw;
        }
    }

    public async Task<IEnumerable<Word>> GetWordsByGroupAsync(int groupId)
    {
        try
        {
            return await _wordRepository.GetWordsByGroupIdAsync(groupId);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving words for group {GroupId}", groupId);
            throw;
        }
    }

    public async Task<Word> AddWordAsync(Word word)
    {
        try
        {
            return await _wordRepository.AddAsync(word);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error adding word {Word}", word.Russian);
            throw;
        }
    }

    public async Task UpdateWordAsync(Word word)
    {
        try
        {
            await _wordRepository.UpdateAsync(word);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating word {WordId}", word.WordsId);
            throw;
        }
    }

    public async Task DeleteWordAsync(int id)
    {
        try
        {
            var word = await _wordRepository.GetByIdAsync(id);
            if (word != null)
            {
                await _wordRepository.DeleteAsync(word);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting word {WordId}", id);
            throw;
        }
    }

    public async Task<(int totalStudied, int totalAvailable)> GetStudyProgressAsync()
    {
        try
        {
            var studied = await _wordRepository.GetStudiedWordsCountAsync();
            var total = await _wordRepository.GetTotalWordsCountAsync();
            return (studied, total);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving study progress");
            throw;
        }
    }
} 