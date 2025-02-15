using Backend.Models;
using Backend.Services.Repositories;

namespace Backend.Services;

public class GroupService : IGroupService
{
    private readonly IGroupRepository _groupRepository;
    private readonly IStudySessionRepository _studySessionRepository;
    private readonly ILogger<GroupService> _logger;

    public GroupService(
        IGroupRepository groupRepository,
        IStudySessionRepository studySessionRepository,
        ILogger<GroupService> logger)
    {
        _groupRepository = groupRepository;
        _studySessionRepository = studySessionRepository;
        _logger = logger;
    }

    public async Task<Group?> GetGroupAsync(int id)
    {
        try
        {
            return await _groupRepository.GetByIdAsync(id);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving group with ID {Id}", id);
            throw;
        }
    }

    public async Task<IEnumerable<Group>> GetAllGroupsAsync(int page = 1, int pageSize = 100)
    {
        try
        {
            var groups = await _groupRepository.GetGroupsWithWordCountAsync();
            return groups.Skip((page - 1) * pageSize).Take(pageSize);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving groups for page {Page}", page);
            throw;
        }
    }

    public async Task<Group?> GetGroupWithWordsAsync(int id)
    {
        try
        {
            return await _groupRepository.GetGroupWithWordsAsync(id);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving group with words for ID {Id}", id);
            throw;
        }
    }

    public async Task<Group> AddGroupAsync(Group group)
    {
        try
        {
            return await _groupRepository.AddAsync(group);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error adding group {Group}", group.Name);
            throw;
        }
    }

    public async Task UpdateGroupAsync(Group group)
    {
        try
        {
            await _groupRepository.UpdateAsync(group);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating group {GroupId}", group.GroupsId);
            throw;
        }
    }

    public async Task DeleteGroupAsync(int id)
    {
        try
        {
            var group = await _groupRepository.GetByIdAsync(id);
            if (group != null)
            {
                await _groupRepository.DeleteAsync(group);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting group {GroupId}", id);
            throw;
        }
    }

    public async Task<int> GetTotalActiveGroupsAsync()
    {
        try
        {
            return await _groupRepository.GetTotalActiveGroupsAsync();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting total active groups count");
            throw;
        }
    }

    public async Task<IEnumerable<StudySession>> GetGroupStudySessionsAsync(int groupId)
    {
        try
        {
            return await _studySessionRepository.GetSessionsByGroupAsync(groupId);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving study sessions for group {GroupId}", groupId);
            throw;
        }
    }
} 