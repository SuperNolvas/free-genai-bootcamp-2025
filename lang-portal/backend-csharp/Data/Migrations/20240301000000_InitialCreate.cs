using System;
using Microsoft.EntityFrameworkCore.Migrations;

namespace Backend.Data.Migrations;

public partial class InitialCreate : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.CreateTable(
            name: "words",
            columns: table => new
            {
                words_id = table.Column<int>(type: "INTEGER", nullable: false)
                    .Annotation("Sqlite:Autoincrement", true),
                russian = table.Column<string>(type: "TEXT", nullable: false),
                transliteration = table.Column<string>(type: "TEXT", nullable: false),
                english = table.Column<string>(type: "TEXT", nullable: false),
                parts = table.Column<string>(type: "TEXT", nullable: true)
            },
            constraints: table =>
            {
                table.PrimaryKey("pk_words", x => x.words_id);
            });

        migrationBuilder.CreateTable(
            name: "groups",
            columns: table => new
            {
                groups_id = table.Column<int>(type: "INTEGER", nullable: false)
                    .Annotation("Sqlite:Autoincrement", true),
                name = table.Column<string>(type: "TEXT", nullable: false)
            },
            constraints: table =>
            {
                table.PrimaryKey("pk_groups", x => x.groups_id);
            });

        migrationBuilder.CreateTable(
            name: "words_groups",
            columns: table => new
            {
                id = table.Column<int>(type: "INTEGER", nullable: false)
                    .Annotation("Sqlite:Autoincrement", true),
                word_id = table.Column<int>(type: "INTEGER", nullable: false),
                group_id = table.Column<int>(type: "INTEGER", nullable: false)
            },
            constraints: table =>
            {
                table.PrimaryKey("pk_words_groups", x => x.id);
                table.ForeignKey(
                    name: "fk_words_groups_words_word_id",
                    column: x => x.word_id,
                    principalTable: "words",
                    principalColumn: "words_id",
                    onDelete: ReferentialAction.Cascade);
                table.ForeignKey(
                    name: "fk_words_groups_groups_group_id",
                    column: x => x.group_id,
                    principalTable: "groups",
                    principalColumn: "groups_id",
                    onDelete: ReferentialAction.Cascade);
            });

        migrationBuilder.CreateTable(
            name: "study_sessions",
            columns: table => new
            {
                id = table.Column<int>(type: "INTEGER", nullable: false)
                    .Annotation("Sqlite:Autoincrement", true),
                group_id = table.Column<int>(type: "INTEGER", nullable: false),
                created_at = table.Column<DateTime>(type: "TEXT", nullable: false),
                study_activity_id = table.Column<int>(type: "INTEGER", nullable: false)
            },
            constraints: table =>
            {
                table.PrimaryKey("pk_study_sessions", x => x.id);
                table.ForeignKey(
                    name: "fk_study_sessions_groups_group_id",
                    column: x => x.group_id,
                    principalTable: "groups",
                    principalColumn: "groups_id",
                    onDelete: ReferentialAction.Cascade);
            });

        migrationBuilder.CreateTable(
            name: "study_activities",
            columns: table => new
            {
                id = table.Column<int>(type: "INTEGER", nullable: false)
                    .Annotation("Sqlite:Autoincrement", true),
                study_session_id = table.Column<int>(type: "INTEGER", nullable: false),
                group_id = table.Column<int>(type: "INTEGER", nullable: false),
                created_at = table.Column<DateTime>(type: "TEXT", nullable: false)
            },
            constraints: table =>
            {
                table.PrimaryKey("pk_study_activities", x => x.id);
                table.ForeignKey(
                    name: "fk_study_activities_study_sessions_study_session_id",
                    column: x => x.study_session_id,
                    principalTable: "study_sessions",
                    principalColumn: "id",
                    onDelete: ReferentialAction.Cascade);
                table.ForeignKey(
                    name: "fk_study_activities_groups_group_id",
                    column: x => x.group_id,
                    principalTable: "groups",
                    principalColumn: "groups_id",
                    onDelete: ReferentialAction.Cascade);
            });

        migrationBuilder.CreateTable(
            name: "word_review_items",
            columns: table => new
            {
                word_id = table.Column<int>(type: "INTEGER", nullable: false),
                study_session_id = table.Column<int>(type: "INTEGER", nullable: false),
                correct = table.Column<bool>(type: "INTEGER", nullable: false),
                created_at = table.Column<DateTime>(type: "TEXT", nullable: false)
            },
            constraints: table =>
            {
                table.PrimaryKey("pk_word_review_items", x => new { x.word_id, x.study_session_id });
                table.ForeignKey(
                    name: "fk_word_review_items_words_word_id",
                    column: x => x.word_id,
                    principalTable: "words",
                    principalColumn: "words_id",
                    onDelete: ReferentialAction.Cascade);
                table.ForeignKey(
                    name: "fk_word_review_items_study_sessions_study_session_id",
                    column: x => x.study_session_id,
                    principalTable: "study_sessions",
                    principalColumn: "id",
                    onDelete: ReferentialAction.Cascade);
            });

        migrationBuilder.CreateIndex(
            name: "ix_words_groups_word_id",
            table: "words_groups",
            column: "word_id");

        migrationBuilder.CreateIndex(
            name: "ix_words_groups_group_id",
            table: "words_groups",
            column: "group_id");

        migrationBuilder.CreateIndex(
            name: "ix_study_sessions_group_id",
            table: "study_sessions",
            column: "group_id");

        migrationBuilder.CreateIndex(
            name: "ix_study_activities_study_session_id",
            table: "study_activities",
            column: "study_session_id");

        migrationBuilder.CreateIndex(
            name: "ix_study_activities_group_id",
            table: "study_activities",
            column: "group_id");

        migrationBuilder.CreateIndex(
            name: "ix_word_review_items_study_session_id",
            table: "word_review_items",
            column: "study_session_id");
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropTable(name: "word_review_items");
        migrationBuilder.DropTable(name: "study_activities");
        migrationBuilder.DropTable(name: "study_sessions");
        migrationBuilder.DropTable(name: "words_groups");
        migrationBuilder.DropTable(name: "words");
        migrationBuilder.DropTable(name: "groups");
    }
} 