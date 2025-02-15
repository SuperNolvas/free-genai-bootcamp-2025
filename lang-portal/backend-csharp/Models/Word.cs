using System.Text.Json;

namespace Backend.Models;

public class Word
{
    public int WordsId { get; set; }
    public required string Russian { get; set; }
    public required string Transliteration { get; set; }
    public required string English { get; set; }
    public JsonDocument? Parts { get; set; }

    // Navigation properties
    public ICollection<WordGroup> WordGroups { get; set; } = new List<WordGroup>();
    public ICollection<WordReviewItem> ReviewItems { get; set; } = new List<WordReviewItem>();
} 