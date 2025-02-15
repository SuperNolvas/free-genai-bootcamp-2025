using Backend.Models;

namespace Backend.Services.Repositories;

public interface IGroupRepository : IRepository<Group>
{
    Task<IEnumerable<Group>> GetGroupsWithWordCountAsync();
    Task<Group?> GetGroupWithWordsAsync(int id);
    Task<int> GetTotalActiveGroupsAsync();
} 