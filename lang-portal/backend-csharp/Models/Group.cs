namespace Backend.Models;

public class Group
{
    public int GroupsId { get; set; }
    public required string Name { get; set; }

    // Navigation properties
    public ICollection<WordGroup> WordGroups { get; set; } = new List<WordGroup>();
    public ICollection<StudySession> StudySessions { get; set; } = new List<StudySession>();
    public ICollection<StudyActivity> StudyActivities { get; set; } = new List<StudyActivity>();
} 