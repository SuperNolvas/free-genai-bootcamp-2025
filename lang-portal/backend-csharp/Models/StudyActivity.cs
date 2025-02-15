namespace Backend.Models;

public class StudyActivity
{
    public int Id { get; set; }
    public int StudySessionId { get; set; }
    public int GroupId { get; set; }
    public DateTime CreatedAt { get; set; }

    // Navigation properties
    public StudySession StudySession { get; set; } = null!;
    public Group Group { get; set; } = null!;
} 