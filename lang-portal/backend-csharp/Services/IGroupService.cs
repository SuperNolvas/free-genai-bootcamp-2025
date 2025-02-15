using Backend.Models;

namespace Backend.Services;

public interface IGroupService
{
    Task<Group?> GetGroupAsync(int id);
    Task<IEnumerable<Group>> GetAllGroupsAsync(int page = 1, int pageSize = 100);
    Task<Group?> GetGroupWithWordsAsync(int id);
    Task<Group> AddGroupAsync(Group group);
    Task UpdateGroupAsync(Group group);
    Task DeleteGroupAsync(int id);
    Task<int> GetTotalActiveGroupsAsync();
    Task<IEnumerable<StudySession>> GetGroupStudySessionsAsync(int groupId);
} 