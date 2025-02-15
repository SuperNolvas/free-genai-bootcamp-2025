using Backend.Models;
using Backend.Data;
using Microsoft.EntityFrameworkCore;

namespace Backend.Services.Repositories;

public class WordRepository : Repository<Word>, IWordRepository
{
    public WordRepository(AppDbContext context) : base(context)
    {
    }

    public async Task<IEnumerable<Word>> GetWordsByGroupIdAsync(int groupId)
    {
        return await _context.Words
            .Include(w => w.WordGroups)
            .Where(w => w.WordGroups.Any(wg => wg.GroupId == groupId))
            .ToListAsync();
    }

    public async Task<int> GetTotalWordsCountAsync()
    {
        return await _context.Words.CountAsync();
    }

    public async Task<int> GetStudiedWordsCountAsync()
    {
        return await _context.Words
            .Where(w => w.ReviewItems.Any())
            .CountAsync();
    }
} 