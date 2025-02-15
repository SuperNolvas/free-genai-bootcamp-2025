using Backend.Models;

namespace Backend.Services.Repositories;

public interface IWordRepository : IRepository<Word>
{
    Task<IEnumerable<Word>> GetWordsByGroupIdAsync(int groupId);
    Task<int> GetTotalWordsCountAsync();
    Task<int> GetStudiedWordsCountAsync();
} 