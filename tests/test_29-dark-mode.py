import pytest
import re
import database.db


@pytest.fixture
def client(monkeypatch, tmp_path):
    """
    Fixture to set up a clean, isolated database for each test run.
    Monkeypatches database.db.DB_PATH to use a temp directory.
    """
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database.db, "DB_PATH", db_path)

    # Import app inside fixture so monkeypatching takes effect
    from app import app as flask_app

    flask_app.config.update({"TESTING": True, "WTF_CSRF_ENABLED": False})

    database.db.init_db(db_path)
    database.db.seed_db(db_path)

    with flask_app.test_client() as client:
        yield client


def test_theme_toggle_visibility_and_accessibility(client):
    """
    Verify that a theme toggle button is visible in the navbar for both logged-in
    and logged-out states, and that it is keyboard-accessible (using a <button> element).
    """
    # 1. Logged-out state
    response_logged_out = client.get("/")
    assert response_logged_out.status_code == 200
    html_logged_out = response_logged_out.data.decode("utf-8")

    # Assert toggle exists, is a <button> element (inherently keyboard accessible), and has correct attributes
    assert 'id="theme-toggle"' in html_logged_out
    assert 'class="theme-toggle"' in html_logged_out
    assert 'aria-label="Toggle dark mode"' in html_logged_out
    # Check that it uses a button tag
    assert "<button" in html_logged_out and "theme-toggle" in html_logged_out

    # 2. Logged-in state
    login_resp = client.post(
        "/login", data={"email": "demo@spendly.com", "password": "demo123"}
    )
    assert login_resp.status_code == 302

    response_logged_in = client.get("/profile")
    assert response_logged_in.status_code == 200
    html_logged_in = response_logged_in.data.decode("utf-8")

    assert 'id="theme-toggle"' in html_logged_in
    assert 'class="theme-toggle"' in html_logged_in
    assert "<button" in html_logged_in and "theme-toggle" in html_logged_in


def test_fouc_prevention_script_in_head(client):
    """
    Verify that there is a blocking/inline script in <head> to prevent FOUC (Flash of Unstyled Content)
    by setting the attribute 'data-theme' before the body is rendered.
    """
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # Extract head section
    head_match = re.search(r"<head>(.*?)</head>", html, re.DOTALL)
    assert head_match is not None, "Could not find <head> block in HTML"
    head_content = head_match.group(1)

    # Check for blocking script setting data-theme from localStorage
    assert "localStorage.getItem" in head_content
    assert "spendly-theme" in head_content
    assert "setAttribute" in head_content
    assert "data-theme" in head_content


def test_light_mode_default_and_icons(client):
    """
    Verify that the default state is light mode (no data-theme attribute on <html> by default)
    and the toggle shows the correct theme icon structure.
    """
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # By default, the html element shouldn't have data-theme="dark" hardcoded
    assert '<html lang="en" data-theme="dark"' not in html
    assert 'id="theme-icon"' in html
    assert (
        "dark_mode" in html
    )  # material symbol name for moon icon (or representation of dark mode transition)


def test_javascript_theme_persistence_and_toggling(client):
    """
    Verify that main.js contains the javascript implementation for:
    1. Querying localStorage for the user's preference 'spendly-theme'.
    2. Event listener that toggles the data-theme attribute on document.documentElement.
    3. Persisting the updated setting to localStorage.
    4. Swapping the icon name (between dark_mode and light_mode).
    """
    response = client.get("/static/js/main.js")
    assert response.status_code == 200
    js_code = response.data.decode("utf-8")

    # LocalStorage key verify
    assert "spendly-theme" in js_code
    assert "localStorage.getItem" in js_code
    assert "localStorage.setItem" in js_code

    # Toggle logic check
    assert "themeToggle" in js_code or "theme-toggle" in js_code
    assert "data-theme" in js_code
    assert "setAttribute" in js_code
    assert "removeAttribute" in js_code
    assert "light_mode" in js_code
    assert "dark_mode" in js_code


def test_dark_mode_css_variables_and_print_override(client):
    """
    Verify that style.css defines the [data-theme="dark"] rules, overriding color variables,
    and has print rules forcing light theme.
    """
    response = client.get("/static/css/style.css")
    assert response.status_code == 200
    css_content = response.data.decode("utf-8")

    # Verify dark theme variables selector
    assert '[data-theme="dark"]' in css_content

    # Ensure key variables are overridden
    dark_block_match = re.search(r'\[data-theme="dark"\]\s*\{([^}]+)\}', css_content)
    assert (
        dark_block_match is not None
    ), 'Could not find [data-theme="dark"] block in style.css'
    dark_properties = dark_block_match.group(1)

    # Check for basic theme variable re-definitions
    assert "--ink" in dark_properties
    assert "--paper" in dark_properties
    assert "--accent" in dark_properties
    assert "--border" in dark_properties
    assert "--success" in dark_properties
    assert "--danger" in dark_properties

    # Ensure print overrides exist to force light theme/color scheme
    assert "@media print" in css_content
    # The print block should specify light color-scheme or override vars
    print_index = css_content.find("@media print")
    print_substring = css_content[print_index : print_index + 1000]
    assert "color-scheme: light" in print_substring or "--ink" in print_substring
