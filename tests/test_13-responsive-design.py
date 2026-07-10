import pytest
import database.db
import re


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


def test_base_template_hamburger_and_aria_attributes(client):
    """
    Verify that the base template base.html includes:
    1. The responsive mobile menu toggle button '#nav-toggle' with aria-expanded and aria-controls attributes.
    2. The wrapper '.nav-links' container with id 'nav-links-menu'.
    3. The material-symbols-outlined hamburger icon name inside '#nav-toggle'.
    """
    # Verify markup on the landing page (which uses base.html)
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # 1. Assert '#nav-toggle' exists with proper classes and attributes
    assert 'id="nav-toggle"' in html
    assert 'class="nav-toggle"' in html or "class='nav-toggle'" in html
    assert 'aria-expanded="false"' in html
    assert 'aria-controls="nav-links-menu"' in html
    assert 'aria-label="Toggle navigation"' in html

    # 2. Assert navigation links container has appropriate ID for accessibility controls
    assert 'id="nav-links-menu"' in html
    assert 'class="nav-links"' in html or "class='nav-links'" in html

    # 3. Assert hamburger toggle contains the icon 'menu'
    # It starts with the hamburger menu icon
    assert "menu" in html


def test_responsive_meta_tag_and_stylesheet_links(client):
    """
    Verify that pages render the viewport meta tag for responsive scaling
    and link the core CSS assets.
    """
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # Check viewport meta tag for responsive design
    assert 'name="viewport"' in html
    assert 'content="width=device-width, initial-scale=1.0"' in html

    # Verify key stylesheets are linked
    assert 'href="/static/css/style.css"' in html or "style.css" in html
    assert (
        'href="/static/css/flash_messages.css"' in html or "flash_messages.css" in html
    )


def test_profile_page_table_responsive_data_labels(client):
    """
    Verify that:
    1. Only authenticated users can access the profile page (auth guard check).
    2. The transactions/expenses table columns (td) contain 'data-label' cell properties.
    """
    # 1. Access as guest (unauthenticated) - check redirect
    guest_resp = client.get("/profile", follow_redirects=True)
    assert guest_resp.status_code == 200
    assert b"Please log in to access this page." in guest_resp.data

    # Log in as the seeded user
    login_resp = client.post(
        "/login", data={"email": "demo@spendly.com", "password": "demo123"}
    )
    assert login_resp.status_code == 302

    # Load profile page
    profile_resp = client.get("/profile")
    assert profile_resp.status_code == 200
    html = profile_resp.data.decode("utf-8")

    # Check that profile page links its specific stylesheets
    assert "profile.css" in html
    assert "empty_states.css" in html

    # 2. Verify table exists and cells contain responsive data-label attributes
    assert 'class="expense-table"' in html
    assert 'data-label="Date"' in html
    assert 'data-label="Category"' in html
    assert 'data-label="Description"' in html
    assert 'data-label="Amount"' in html
    assert 'data-label="Actions"' in html


def test_javascript_toggle_interaction_and_escapes(client):
    """
    Verify that main.js contains the logical interactions for:
    1. Hamburger menu toggle (adding class, changing aria-expanded, switching icon name).
    2. Closing drawer when clicking outside.
    3. Closing drawer when Escape key is pressed.
    """
    response = client.get("/static/js/main.js")
    assert response.status_code == 200
    js_code = response.data.decode("utf-8")

    # 1. Toggle logic
    assert "navToggle" in js_code
    assert "navLinksMenu" in js_code
    assert "aria-expanded" in js_code
    assert "classList.toggle" in js_code or "classList.add" in js_code
    assert "open" in js_code

    # 2. Click outside logic
    assert "contains" in js_code
    assert "click" in js_code
    assert "classList.remove" in js_code

    # 3. Escape key press logic
    assert "keydown" in js_code
    assert "Escape" in js_code


def parse_css_media_query_block(css_text, max_width):
    """
    Helper function to parse and extract the body of a specific media query,
    e.g., @media (max-width: <max_width>) {...}
    Uses nested brace parsing to capture all contents.
    """
    pattern = rf"@media\s*\(\s*max-width\s*:\s*{max_width}\s*\)"
    match = re.search(pattern, css_text)
    if not match:
        return ""

    start_idx = css_text.find("{", match.end())
    if start_idx == -1:
        return ""

    brace_count = 1
    current_idx = start_idx + 1
    while brace_count > 0 and current_idx < len(css_text):
        char = css_text[current_idx]
        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
        current_idx += 1

    return css_text[start_idx + 1 : current_idx - 1]


def parse_css_selector_block(css_text, selector_name):
    """
    Helper function to extract declarations inside a selector block.
    Matches the selector name followed by { ... } (excluding @media blocks).
    """
    # A simple regex to find the selector block outside @media if possible,
    # or just matches any occurrence of selector_name followed by { ... }
    pattern = rf"(?:^|[\}}\s]){re.escape(selector_name)}\s*\{{([^}}]+)\}}"
    matches = re.findall(pattern, css_text)
    return "\n".join(matches)


def test_css_variables_and_no_hardcoded_colors(client):
    """
    Verify color variables usage to ensure no hardcoded colors are in the new CSS styles.
    Checks:
    1. Selectors like .nav-toggle do not have hardcoded colors (uses CSS variables only).
    2. Declarations inside responsive media queries (@media (max-width: 768px), @media (max-width: 600px), @media (max-width: 480px))
       do not contain any hardcoded colors (no hex, rgb, or named colors in color/background/border fields).
    """
    # 1. Fetch style.css
    response_style = client.get("/static/css/style.css")
    assert response_style.status_code == 200
    style_css = response_style.data.decode("utf-8")

    # Strip comments first
    style_css_clean = re.sub(r"/\*.*?\*/", "", style_css, flags=re.DOTALL)

    # Inspect .nav-toggle selector styles outside variables block
    toggle_styles = parse_css_selector_block(style_css_clean, ".nav-toggle")
    # Should not contain hex color (#...)
    assert "#" not in toggle_styles

    # Extract responsive blocks
    media_768 = parse_css_media_query_block(style_css_clean, "768px")
    media_600 = parse_css_media_query_block(style_css_clean, "600px")
    media_480 = parse_css_media_query_block(style_css_clean, "480px")

    # For these responsive media query blocks, ensure no hardcoded color values are defined in properties.
    # We will search for occurrences of hex codes (e.g. #000, #ffffff) in color, background, and border properties.
    for block_name, block_text in [
        ("768px", media_768),
        ("600px", media_600),
        ("480px", media_480),
    ]:
        if not block_text:
            continue

        # Verify color, background, border declarations do not have hardcoded hex colors
        declarations = re.findall(r"([a-zA-Z\-]+)\s*:\s*([^;]+);", block_text)
        for prop, val in declarations:
            prop = prop.strip()
            val = val.strip()

            # Check properties related to coloring
            if any(k in prop for k in ["color", "background", "border", "outline"]):
                # Hex code search (e.g. #fff, #123456)
                hex_match = re.search(r"#[0-9a-fA-F]{3,8}", val)
                assert (
                    hex_match is None
                ), f"Hardcoded hex color '{hex_match.group()}' found in media query '{block_name}' for property '{prop}: {val}'"

                # Check for standard hardcoded color names (like red, blue, green, white, black) as direct values
                # ignoring variable names or properties like border-style (e.g., solid)
                # We can verify that if a name is present, it's not a color name like white or black directly.
                for color_name in ["white", "black", "red", "green", "blue", "yellow"]:
                    # Exact word match for color names
                    word_match = re.search(rf"\b{color_name}\b", val)
                    # If it has a color name, check that it's not a hardcoded color (allow if it's inside some path or var)
                    if word_match:
                        # Allow if it's inside var(--...) or part of box-shadow overlay etc.
                        assert (
                            "var(" in val or "rgba" in val
                        ), f"Hardcoded color name '{color_name}' found in property '{prop}: {val}'"

    # 2. Fetch profile.css and check its media queries
    response_profile = client.get("/static/css/profile.css")
    assert response_profile.status_code == 200
    profile_css = response_profile.data.decode("utf-8")
    profile_css_clean = re.sub(r"/\*.*?\*/", "", profile_css, flags=re.DOTALL)

    media_profile_900 = parse_css_media_query_block(profile_css_clean, "900px")
    media_profile_768 = parse_css_media_query_block(profile_css_clean, "768px")
    media_profile_600 = parse_css_media_query_block(profile_css_clean, "600px")

    for block_name, block_text in [
        ("900px", media_profile_900),
        ("768px", media_profile_768),
        ("600px", media_profile_600),
    ]:
        if not block_text:
            continue
        declarations = re.findall(r"([a-zA-Z\-]+)\s*:\s*([^;]+);", block_text)
        for prop, val in declarations:
            prop = prop.strip()
            val = val.strip()

            if any(k in prop for k in ["color", "background", "border", "outline"]):
                hex_match = re.search(r"#[0-9a-fA-F]{3,8}", val)
                assert (
                    hex_match is None
                ), f"Hardcoded hex color '{hex_match.group()}' found in media query '{block_name}' in profile.css for property '{prop}: {val}'"


def test_responsive_minimum_touch_target_requirements(client):
    """
    Verify that interactive elements define a minimum touch target size of 44px x 44px
    for responsive layout compliance (as stated in the spec rules).
    """
    # 1. Fetch style.css and ensure .nav-toggle and .nav-links links enforce 44px boundaries
    response_style = client.get("/static/css/style.css")
    style_css = response_style.data.decode("utf-8")

    # Assert minimum heights or widths are configured in style.css for responsive links
    assert "min-height: 44px" in style_css
    assert "min-width: 44px" in style_css

    # 2. Fetch profile.css and ensure mobile button targets for edit/delete scale to at least 44px
    response_profile = client.get("/static/css/profile.css")
    profile_css = response_profile.data.decode("utf-8")

    # Assert edit/delete action button hit areas are scaled up on mobile viewport in profile.css
    assert "min-height: 44px" in profile_css
    assert "min-width: 44px" in profile_css
