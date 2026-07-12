import os


def test_readme_exists():
    """Verify that README.md exists at the project root."""
    assert os.path.exists("README.md"), "README.md file does not exist at the root"


def test_readme_contains_sections_and_symbol():
    """Verify that README.md contains required sections and the Unicode symbol ◈."""
    assert os.path.exists("README.md"), "README.md file does not exist at the root"

    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    # Check for Unicode symbol ◈
    assert "◈" in content, "README.md does not contain the Unicode symbol ◈"

    # Check for sections like Features, Tech Stack, Installation/Setup (or variants thereof in README)
    # We will search for common variations of headings
    features_found = any(
        x in content.lower() for x in ["features", "key features", "core features"]
    )
    tech_stack_found = any(
        x in content.lower()
        for x in ["tech stack", "technology stack", "architectural constraints"]
    )
    setup_found = any(
        x in content.lower()
        for x in ["installation", "setup", "quick start", "installation & quick start"]
    )

    assert features_found, "README.md does not contain a Features section"
    assert tech_stack_found, "README.md does not contain a Tech Stack section"
    assert setup_found, "README.md does not contain an Installation/Setup section"


def test_readme_contains_detailed_contents():
    """Verify that README.md contains project architecture, database schema, and dark mode mentions."""
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read().lower()

    # Check for Dark Mode mention
    assert "dark mode" in content, "README.md does not mention Dark Mode"

    # Check for Database Schema details
    schema_found = any(x in content for x in ["database schema", "schema", "sqlite"])
    assert schema_found, "README.md does not mention Database Schema"

    # Check for Project Directory Structure/Architecture details
    architecture_found = any(
        x in content
        for x in ["directory structure", "architecture overview", "project directory"]
    )
    assert (
        architecture_found
    ), "README.md does not mention Project Directory Structure / Architecture"
