using Microsoft.EntityFrameworkCore;
using Backend.Data;
using Backend.Services;

var builder = WebApplication.CreateBuilder(args);

// Add DbContext
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlite(builder.Configuration.GetConnectionString("DefaultConnection")));

// Add services to the container.
builder.Services.AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.SnakeCaseNaming;
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

// Register services
builder.Services.AddScoped<DataSeeder>();
builder.Services.AddScoped<DatabaseManager>();

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