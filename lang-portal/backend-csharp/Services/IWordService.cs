using Backend.Models;

namespace Backend.Services;

public interface IWordService
{
    Task<Word?> GetWordAsync(int id);
    Task<IEnumerable<Word>> GetAllWordsAsync(int page = 1, int pageSize = 100);
    Task<IEnumerable<Word>> GetWordsByGroupAsync(int groupId);
    Task<Word> AddWordAsync(Word word);
    Task UpdateWordAsync(Word word);
    Task DeleteWordAsync(int id);
    Task<(int totalStudied, int totalAvailable)> GetStudyProgressAsync();
} 