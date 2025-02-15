using Microsoft.EntityFrameworkCore;
using Backend.Data;
using Backend.Services;
using Backend.Services.Repositories;
using System.Text.Json.Serialization;

var builder = WebApplication.CreateBuilder(args);

// Add DbContext
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlite(builder.Configuration.GetConnectionString("DefaultConnection")));

// Add services to the container.
builder.Services.AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.PropertyNamingPolicy = new SnakeCaseNamingPolicy();
    });

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Configure CORS for development
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(builder =>
    {
        builder.AllowAnyOrigin()
               .AllowAnyMethod()
               .AllowAnyHeader();
    });
});

// Register repositories
builder.Services.AddScoped(typeof(IRepository<>), typeof(Repository<>));
builder.Services.AddScoped<IWordRepository, WordRepository>();
builder.Services.AddScoped<IGroupRepository, GroupRepository>();
builder.Services.AddScoped<IStudySessionRepository, StudySessionRepository>();
builder.Services.AddScoped<IWordReviewRepository, WordReviewRepository>();
builder.Services.AddScoped<IStudyActivityRepository, StudyActivityRepository>();

// Register services
builder.Services.AddScoped<IWordService, WordService>();
builder.Services.AddScoped<IGroupService, GroupService>();
builder.Services.AddScoped<IStudySessionService, StudySessionService>();
builder.Services.AddScoped<IStudyActivityService, StudyActivityService>();
builder.Services.AddScoped<DatabaseHealthCheck>();
builder.Services.AddScoped<DataSeeder>();
builder.Services.AddScoped<DatabaseManager>();

// Add health checks
builder.Services.AddHealthChecks()
    .AddCheck<DatabaseHealthCheck>("database_health_check");

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseCors();
app.UseAuthorization();
app.MapControllers();

// Map health checks endpoint
app.MapHealthChecks("/health");

// Ensure the database directory exists
Directory.CreateDirectory(Path.Combine(Directory.GetCurrentDirectory(), "db"));

// Initialize database after app is built
using (var scope = app.Services.CreateScope())
{
    var dbManager = scope.ServiceProvider.GetRequiredService<DatabaseManager>();
    await dbManager.InitializeDatabaseAsync();
    await dbManager.MigrateDatabaseAsync();
    
    if (app.Environment.IsDevelopment())
    {
        await dbManager.SeedDatabaseAsync();
    }
}

app.Run();

public partial class Program { } 