namespace Backend.Models;

public class WordReviewItem
{
    public int WordId { get; set; }
    public int StudySessionId { get; set; }
    public bool Correct { get; set; }
    public DateTime CreatedAt { get; set; }

    // Navigation properties
    public Word Word { get; set; } = null!;
    public StudySession StudySession { get; set; } = null!;
} 