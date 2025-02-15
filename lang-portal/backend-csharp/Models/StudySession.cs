namespace Backend.Models;

public class StudySession
{
    public int Id { get; set; }
    public int GroupId { get; set; }
    public DateTime CreatedAt { get; set; }
    public int StudyActivityId { get; set; }

    // Navigation properties
    public Group Group { get; set; } = null!;
    public StudyActivity StudyActivity { get; set; } = null!;
    public ICollection<WordReviewItem> ReviewItems { get; set; } = new List<WordReviewItem>();
} 