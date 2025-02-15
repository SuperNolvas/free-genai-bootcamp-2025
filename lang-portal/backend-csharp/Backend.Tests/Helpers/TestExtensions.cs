using System.Net.Http.Headers;

namespace Backend.Tests.Helpers;

public static class TestExtensions
{
    public static int GetResourceIdFromLocation(this HttpResponseMessage response)
    {
        var location = response.Headers.Location?.ToString() ?? 
            throw new InvalidOperationException("Location header is missing");
        return int.Parse(location.Split('/').Last());
    }
} 