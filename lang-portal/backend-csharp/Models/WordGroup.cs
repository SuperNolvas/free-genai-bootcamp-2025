namespace Backend.Models;

public class WordGroup
{
    public int Id { get; set; }
    public int WordId { get; set; }
    public int GroupId { get; set; }

    // Navigation properties
    public Word Word { get; set; } = null!;
    public Group Group { get; set; } = null!;
} 