using Backend.Models;
using Backend.Data;
using Microsoft.EntityFrameworkCore;

namespace Backend.Services.Repositories;

public class WordReviewRepository : Repository<WordReviewItem>, IWordReviewRepository
{
    public WordReviewRepository(AppDbContext context) : base(context)
    {
    }

    public async Task<double> GetSuccessRateAsync()
    {
        var reviews = await _context.WordReviewItems.ToListAsync();
        if (!reviews.Any()) return 0;

        return (double)reviews.Count(r => r.Correct) / reviews.Count * 100;
    }

    public async Task<IEnumerable<WordReviewItem>> GetReviewsBySessionAsync(int sessionId)
    {
        return await _context.WordReviewItems
            .Include(wr => wr.Word)
            .Where(wr => wr.StudySessionId == sessionId)
            .OrderByDescending(wr => wr.CreatedAt)
            .ToListAsync();
    }

    public async Task<IEnumerable<WordReviewItem>> GetReviewsByWordAsync(int wordId)
    {
        return await _context.WordReviewItems
            .Include(wr => wr.StudySession)
            .Where(wr => wr.WordId == wordId)
            .OrderByDescending(wr => wr.CreatedAt)
            .ToListAsync();
    }
} 