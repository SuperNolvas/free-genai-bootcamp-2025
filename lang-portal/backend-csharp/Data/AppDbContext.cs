using Microsoft.EntityFrameworkCore;
using Backend.Models;

namespace Backend.Data;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
    {
    }

    public DbSet<Word> Words => Set<Word>();
    public DbSet<Group> Groups => Set<Group>();
    public DbSet<WordGroup> WordGroups => Set<WordGroup>();
    public DbSet<StudySession> StudySessions => Set<StudySession>();
    public DbSet<StudyActivity> StudyActivities => Set<StudyActivity>();
    public DbSet<WordReviewItem> WordReviewItems => Set<WordReviewItem>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // Configure snake_case table and column names
        foreach (var entity in modelBuilder.Model.GetEntityTypes())
        {
            entity.SetTableName(entity.GetTableName()?.ToSnakeCase());

            foreach (var property in entity.GetProperties())
            {
                property.SetColumnName(property.GetColumnName().ToSnakeCase());
            }
        }

        // Configure relationships
        modelBuilder.Entity<WordGroup>()
            .HasKey(wg => wg.Id);

        modelBuilder.Entity<WordGroup>()
            .HasOne(wg => wg.Word)
            .WithMany(w => w.WordGroups)
            .HasForeignKey(wg => wg.WordId);

        modelBuilder.Entity<WordGroup>()
            .HasOne(wg => wg.Group)
            .WithMany(g => g.WordGroups)
            .HasForeignKey(wg => wg.GroupId);

        modelBuilder.Entity<StudySession>()
            .HasOne(ss => ss.Group)
            .WithMany(g => g.StudySessions)
            .HasForeignKey(ss => ss.GroupId);

        modelBuilder.Entity<StudyActivity>()
            .HasOne(sa => sa.Group)
            .WithMany(g => g.StudyActivities)
            .HasForeignKey(sa => sa.GroupId);

        modelBuilder.Entity<WordReviewItem>()
            .HasKey(wri => new { wri.WordId, wri.StudySessionId });

        modelBuilder.Entity<WordReviewItem>()
            .HasOne(wri => wri.Word)
            .WithMany(w => w.ReviewItems)
            .HasForeignKey(wri => wri.WordId);

        modelBuilder.Entity<WordReviewItem>()
            .HasOne(wri => wri.StudySession)
            .WithMany(ss => ss.ReviewItems)
            .HasForeignKey(wri => wri.StudySessionId);
    }
}

// Extension method for snake_case conversion
public static class StringExtensions
{
    public static string ToSnakeCase(this string text)
    {
        if (text == null)
        {
            throw new ArgumentNullException(nameof(text));
        }
        if (text.Length < 2)
        {
            return text;
        }
        var sb = new System.Text.StringBuilder();
        sb.Append(char.ToLowerInvariant(text[0]));
        for (int i = 1; i < text.Length; ++i)
        {
            char c = text[i];
            if (char.IsUpper(c))
            {
                sb.Append('_');
                sb.Append(char.ToLowerInvariant(c));
            }
            else
            {
                sb.Append(c);
            }
        }
        return sb.ToString();
    }
} 