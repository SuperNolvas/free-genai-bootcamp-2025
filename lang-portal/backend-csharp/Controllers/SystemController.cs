using Microsoft.AspNetCore.Mvc;
using Backend.Services;

namespace Backend.Controllers;

[ApiController]
[Route("api")]
public class SystemController : ControllerBase
{
    private readonly DatabaseManager _databaseManager;
    private readonly ILogger<SystemController> _logger;

    public SystemController(
        DatabaseManager databaseManager,
        ILogger<SystemController> logger)
    {
        _databaseManager = databaseManager;
        _logger = logger;
    }

    [HttpPost("reset_history")]
    public async Task<IActionResult> ResetHistory()
    {
        try
        {
            await _databaseManager.ResetDatabaseAsync();
            return Ok(new
            {
                success = true,
                message = "Study history has been reset"
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error resetting study history");
            return StatusCode(500, new { message = "An error occurred while resetting study history" });
        }
    }

    [HttpPost("full_reset")]
    public async Task<IActionResult> FullReset()
    {
        try
        {
            await _databaseManager.ResetDatabaseAsync();
            await _databaseManager.SeedDatabaseAsync();
            
            return Ok(new
            {
                success = true,
                message = "System has been fully reset"
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error performing full system reset");
            return StatusCode(500, new { message = "An error occurred while performing full system reset" });
        }
    }
} 