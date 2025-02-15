using System.Text.Json;
using System.Text.RegularExpressions;

namespace Backend.Services;

public class SnakeCaseNamingPolicy : JsonNamingPolicy
{
    public override string ConvertName(string name)
    {
        if (string.IsNullOrEmpty(name))
            return name;

        var pattern = @"[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+";
        var result = Regex.Matches(name, pattern)
            .Select(m => m.Value.ToLowerInvariant());

        return string.Join("_", result);
    }
} 