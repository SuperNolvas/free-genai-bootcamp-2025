using Backend.Models;
using Backend.Data;
using Microsoft.EntityFrameworkCore;

namespace Backend.Services.Repositories;

public class StudyActivityRepository : Repository<StudyActivity>, IStudyActivityRepository
{
    public StudyActivityRepository(AppDbContext context) : base(context)
    {
    }

    public async Task<IEnumerable<StudyActivity>> GetActivitiesByGroupAsync(int groupId)
    {
        return await _context.StudyActivities
            .Where(sa => sa.GroupId == groupId)
            .OrderByDescending(sa => sa.CreatedAt)
            .ToListAsync();
    }

    public async Task<StudyActivity?> GetActivityWithDetailsAsync(int id)
    {
        return await _context.StudyActivities
            .Include(sa => sa.Group)
            .Include(sa => sa.StudySession)
            .FirstOrDefaultAsync(sa => sa.Id == id);
    }
} 