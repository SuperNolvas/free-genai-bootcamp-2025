using Backend.Models;
using Backend.Data;
using Microsoft.EntityFrameworkCore;

namespace Backend.Services.Repositories;

public class StudySessionRepository : Repository<StudySession>, IStudySessionRepository
{
    public StudySessionRepository(AppDbContext context) : base(context)
    {
    }

    public async Task<StudySession?> GetLatestSessionAsync()
    {
        return await _context.StudySessions
            .Include(ss => ss.Group)
            .Include(ss => ss.StudyActivity)
            .OrderByDescending(ss => ss.CreatedAt)
            .FirstOrDefaultAsync();
    }

    public async Task<IEnumerable<StudySession>> GetSessionsByGroupAsync(int groupId)
    {
        return await _context.StudySessions
            .Include(ss => ss.StudyActivity)
            .Where(ss => ss.GroupId == groupId)
            .OrderByDescending(ss => ss.CreatedAt)
            .ToListAsync();
    }

    public async Task<int> GetStudyStreakDaysAsync()
    {
        var sessions = await _context.StudySessions
            .OrderByDescending(ss => ss.CreatedAt)
            .Select(ss => ss.CreatedAt.Date)
            .Distinct()
            .ToListAsync();

        int streak = 0;
        var currentDate = DateTime.UtcNow.Date;

        foreach (var sessionDate in sessions)
        {
            if (sessionDate == currentDate.AddDays(-streak))
            {
                streak++;
            }
            else
            {
                break;
            }
        }

        return streak;
    }
} 