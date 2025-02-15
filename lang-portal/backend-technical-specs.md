`## Business Goal:

A language learning school wants to build a prototype of a learning portal which will act as three things:

*   Inventory of possible vocabulary that can be learned
*   Act as a Learning record store (LRS), providing correct and wrong scores on practiced vocabulary
*   A unified launchpad to launch different learning apps

## Technical Requirements

*   The backend will be built using **C#**
*   The database will be **SQLite3**
*   The API will be built using **ASP.NET Core Web API**
*   The API will always return **JSON**
*   There will be **no authentication or authorization**
*   Everything will be treated as a **single user**

## Directory Structure
```tree
backend_cs/
├── Controllers/      # ASP.NET Core Web API Controllers
├── Models/           # Data models and entities
├── Services/          # Business logic and application services
├── Data/              # Database context and data access logic
│   ├── Migrations/   # Entity Framework Core Migrations
│   └── SeedData/    # For initial data population
├── db/                # Database related files (can be outside if preferred)
│   └── words.db
├── appsettings.json   # Application configuration
├── Program.cs         # Application entry point
├── Backend.csproj     # C# project file
```
`## Database Schema

Our database will be a single SQLite database called `words.db` that will be in the `db` folder of the `backend_cs` directory.

We have the following tables:

*   **words** - stored vocabulary
    *   `wordsId` INTEGER (Primary Key)
    *   `russian` TEXT
    *   `transliteration` TEXT
    *   `english` TEXT
    *   `parts` JSON (Optional: could describe grammatical parts of speech, etc.)

*   **words_groups** - join table for words and groups (many-to-many)
    *   `id` INTEGER (Primary Key)
    *   `word_id` INTEGER (Foreign Key referencing `words.wordsId`)
    *   `group_id` INTEGER (Foreign Key referencing `groups.groupsId`)

*   **groups** - thematic groups of words
    *   `groupsId` INTEGER (Primary Key)
    *   `name` TEXT

*   **study_sessions** - records of study sessions grouping word_review_items
    *   `id` INTEGER (Primary Key)
    *   `group_id` INTEGER (Foreign Key referencing `groups.groupsId`)
    *   `created_at` DATETIME
    *   `study_activity_id` INTEGER (Foreign Key referencing `study_activities.id`)

*   **study_activities** - a specific study activity, linking a study session to a group
    *   `id` INTEGER (Primary Key)
    *   `study_session_id` INTEGER (Foreign Key referencing `study_sessions.id`)
    *   `group_id` INTEGER (Foreign Key referencing `groups.groupsId`)
    *   `created_at` DATETIME

*   **word_review_items** - a record of word practice, determining if the word was correct or not
    *   `word_id` INTEGER (Foreign Key referencing `words.wordsId`)
    *   `study_session_id` INTEGER (Foreign Key referencing `study_sessions.id`)
    *   `correct` BOOLEAN
    *   `created_at` DATETIME

## API Endpoints

### GET /api/dashboard/last_study_session

Returns information about the most recent study session.

**JSON Response**

```json
{
  "id": 123,
  "group_id": 456,
  "created_at": "2025-02-08T17:20:23-05:00",
  "study_activity_id": 789,
  "group_id": 456,
  "group_name": "Basic Greetings"
}
```
### GET /api/dashboard/study_progress

Returns study progress statistics. Please note that the frontend will determine the progress bar based on total words studied and total available words.

**JSON Response**
```JSON

{
  "total_words_studied": 3,
  "total_available_words": 124
}
```
### GET /api/dashboard/quick-stats

Returns quick overview statistics.

**JSON Response**

```JSON

{
  "success_rate": 80.0,
  "total_study_sessions": 4,
  "total_active_groups": 3,
  "study_streak_days": 4
}
```
### GET /api/study_activities/:id

**JSON Response**

```JSON

{
  "id": 1,
  "name": "Vocabulary Quiz",
  "thumbnail_url": "https://example.com/thumbnail.jpg",
  "description": "Practice your vocabulary with flashcards"
}
```
### GET /api/study_activities/:id/study_sessions

- Pagination with 100 items per page

```JSON

{
  "items": [
    {
      "id": 123,
      "activity_name": "Vocabulary Quiz",
      "group_name": "Basic Greetings",
      "start_time": "2025-02-08T17:20:23-05:00",
      "end_time": "2025-02-08T17:30:23-05:00",
      "review_items_count": 20
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 100,
    "items_per_page": 20
  }
}
```
### POST /api/study_activities

**Request Params**

- `group_id` INTEGER
- `study_activity_id` INTEGER

**JSON Response**

```JSON

{ "id": 124, "group_id": 123 }
```
### GET /api/words

- Pagination with 100 items per page

**JSON Response**

```JSON

{
  "items": [
    {
      "russian": "здравствуйте",
      "transliteration": "zdravstvuyte",
      "english": "hello",
      "correct_count": 5,
      "wrong_count": 2
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 500,
    "items_per_page": 100
  }
}
```
### GET /api/words/:id

**JSON Response**

```JSON

{
  "russian": "здравствуйте",
  "transliteration": "zdravstvuyte",
  "english": "hello",
  "stats": {
    "correct_count": 5,
    "wrong_count": 2
  },
  "groups": [
    {
      "id": 1,
      "name": "Basic Greetings"
    }
  ]
}
```
### GET /api/groups

- Pagination with 100 items per page

**JSON Response**

```JSON

{
  "items": [
    {
      "id": 1,
      "name": "Basic Greetings",
      "word_count": 20
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_items": 10,
    "items_per_page": 100
  }
}
```
### GET /api/groups/:id

**JSON Response**

```JSON

{
  "id": 1,
  "name": "Basic Greetings",
  "stats": {
    "total_word_count": 20
  }
}
```
### GET /api/groups/:id/words

**JSON Response**

```JSON

{
  "items": [
    {
      "russian": "здравствуйте",
      "transliteration": "zdravstvuyte",
      "english": "hello",
      "correct_count": 5,
      "wrong_count": 2
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_items": 20,
    "items_per_page": 100
  }
}
```
### GET /api/groups/:id/study_sessions

**JSON Response**

```JSON

{
  "items": [
    {
      "id": 123,
      "activity_name": "Vocabulary Quiz",
      "group_name": "Basic Greetings",
      "start_time": "2025-02-08T17:20:23-05:00",
      "end_time": "2025-02-08T17:30:23-05:00",
      "review_items_count": 20
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_items": 5,
    "items_per_page": 100
  }
}
```
### GET /api/study_sessions

- Pagination with 100 items per page

**JSON Response**

```JSON

{
  "items": [
    {
      "id": 123,
      "activity_name": "Vocabulary Quiz",
      "group_name": "Basic Greetings",
      "start_time": "2025-02-08T17:20:23-05:00",
      "end_time": "2025-02-08T17:30:23-05:00",
      "review_items_count": 20
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 100,
    "items_per_page": 100
  }
}
```
### GET /api/study_sessions/:id

**JSON Response**

```JSON

{
  "id": 123,
  "activity_name": "Vocabulary Quiz",
  "group_name": "Basic Greetings",
  "start_time": "2025-02-08T17:20:23-05:00",
  "end_time": "2025-02-08T17:30:23-05:00",
  "review_items_count": 20
}
```
### GET /api/study_sessions/:id/words

- Pagination with 100 items per page

**JSON Response**

```JSON

{
  "items": [
    {
      "russian": "здравствуйте",
      "transliteration": "zdravstvuyte",
      "english": "hello",
      "correct_count": 5,
      "wrong_count": 2
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_items": 20,
    "items_per_page": 100
  }
}
```
### POST /api/reset_history

**JSON Response**

```JSON

{
  "success": true,
  "message": "Study history has been reset"
}
```
### POST /api/full_reset

**JSON Response**

```JSON

{
  "success": true,
  "message": "System has been fully reset"
}
```
### POST /api/study_sessions/:id/words/:word_id/review

**Request Params**

- `id` (study_session_id) INTEGER
- `word_id` INTEGER
- `correct` BOOLEAN

**Request Payload**

```JSON

{
  "correct": true
}
```
**JSON Response**

```JSON

{
  "success": true,
  "word_id": 1,
  "study_session_id": 123,
  "correct": true,
  "created_at": "2025-02-08T17:33:07-05:00"
}
```
## Task Runner Tasks

Let's list out possible tasks we need for our Russian language portal.

### Initialize Database

This task will initialize the SQLite database called `words.db`.

### Migrate Database

This task will run a series of migration SQL files on the database.
Migrations live in the `Migrations` folder. The migration files will be run in order of their file name. The file names should look like this:

`0001_init.sql
0002_create_words_table.sql`

### Seed Data

This task will import JSON files and transform them into target data for our database.
All seed files live in the `SeedData` folder.
In our task, we should have DSL to specify each seed file and its expected group word name.

**Example Seed Data Structure (for JSON seed files):**

```JSON

[
  {
    "russian": "платить",
    "transliteration": "platit",
    "english": "to pay"
  },
]
```
