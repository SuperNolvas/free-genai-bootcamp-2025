using Backend.Models;

namespace Backend.Services.Repositories;

public interface IWordReviewRepository : IRepository<WordReviewItem>
{
    Task<double> GetSuccessRateAsync();
    Task<IEnumerable<WordReviewItem>> GetReviewsBySessionAsync(int sessionId);
    Task<IEnumerable<WordReviewItem>> GetReviewsByWordAsync(int wordId);
} 