using Backend.Models;
using Backend.Data;
using Microsoft.EntityFrameworkCore;

namespace Backend.Services.Repositories;

public class GroupRepository : Repository<Group>, IGroupRepository
{
    public GroupRepository(AppDbContext context) : base(context)
    {
    }

    public async Task<IEnumerable<Group>> GetGroupsWithWordCountAsync()
    {
        return await _context.Groups
            .Include(g => g.WordGroups)
            .Select(g => new Group
            {
                GroupsId = g.GroupsId,
                Name = g.Name,
                WordGroups = g.WordGroups
            })
            .ToListAsync();
    }

    public async Task<Group?> GetGroupWithWordsAsync(int id)
    {
        return await _context.Groups
            .Include(g => g.WordGroups)
                .ThenInclude(wg => wg.Word)
            .FirstOrDefaultAsync(g => g.GroupsId == id);
    }

    public async Task<int> GetTotalActiveGroupsAsync()
    {
        return await _context.Groups
            .Where(g => g.WordGroups.Any())
            .CountAsync();
    }
} 