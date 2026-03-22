import time
import os
import random
from playwright.sync_api import sync_playwright
from filter import is_lead
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("REDDIT_USERNAME")
PASSWORD = os.getenv("REDDIT_PASSWORD")

SUBREDDIT_URL = "https://www.reddit.com/r/startups/new/"
SESSION_FILE = "state.json"


def human_delay(min_s=2, max_s=5):
    time.sleep(random.uniform(min_s, max_s))


def login(page, context):
    print("🔐 Logging in via form...")
    page.goto("https://www.reddit.com/login")
    human_delay(3, 5)

    # Wait for page to fully load
    page.wait_for_load_state("networkidle")
    human_delay(1, 2)

    # The inputs are inside shadow DOM custom elements.
    # We use JavaScript to reach them directly.
    page.evaluate(f"""
        document.querySelector('faceplate-text-input#login-username')
            .shadowRoot.querySelector('input').value = '';
    """)

    # Type into username field via JS focus + keyboard
    page.evaluate("""
        document.querySelector('faceplate-text-input#login-username')
            .shadowRoot.querySelector('input').focus();
    """)
    human_delay(0.3, 0.7)
    page.keyboard.type(USERNAME, delay=80)
    human_delay(0.5, 1)

    # Move to password field
    page.evaluate("""
        document.querySelector('faceplate-text-input#login-password')
            .shadowRoot.querySelector('input').focus();
    """)
    human_delay(0.3, 0.7)
    page.keyboard.type(PASSWORD, delay=80)
    human_delay(1, 2)

    # Wait for the Login button to become enabled
    # It starts disabled and enables once both fields have values
    print("⏳ Waiting for Log In button to enable...")
    try:
        page.wait_for_function(
            """() => {
                const btn = document.querySelector('button.login');
                return btn && !btn.disabled;
            }""",
            timeout=15000
        )
    except Exception as e:
        print(f"⚠️ Button wait failed: {e}, trying to click anyway...")

    human_delay(0.5, 1)

    # Click the Log In button via JS to bypass shadow DOM issues
    page.evaluate("""
        document.querySelector('button.login').click();
    """)

    print("⏳ Waiting for login redirect...")
    try:
        page.wait_for_url(lambda url: "login" not in url, timeout=30000)
    except:
        print("⚠️ Login redirect timed out — check credentials or try again.")
        return

    page.wait_for_load_state("networkidle")
    print("✅ Logged in successfully")

    context.storage_state(path=SESSION_FILE)
    print("✅ Session saved")


def is_logged_in(page):
    """Check if current session is valid."""
    page.goto("https://www.reddit.com/")
    human_delay(2, 3)
    try:
        page.wait_for_selector("a[href='/login/']", timeout=4000)
        return False
    except:
        return True


def get_post_title(post):
    """
    Extract post title from an article element.
    Reddit uses shadow DOM inside faceplate-screen-reader-content,
    so h2/h3 inner_text() returns empty. We extract from the anchor instead.
    """
    try:
        # Best source: aria-label on the full-post-link anchor
        title = post.locator("a[slot='full-post-link']").first.get_attribute("aria-label")
        if title and title.strip():
            return title.strip()
    except:
        pass

    try:
        # Fallback: inner_text() on the screen-reader content element
        # (works when shadowrootmode is open and Playwright can pierce it)
        title = post.locator("faceplate-screen-reader-content").first.inner_text()
        if title and title.strip():
            return title.strip()
    except:
        pass

    try:
        # Last resort: pull title from the href slug of the anchor
        href = post.locator("a[slot='full-post-link']").first.get_attribute("href") or ""
        # href pattern: /r/subreddit/comments/<id>/<slug>/
        parts = [p for p in href.split("/") if p]
        if len(parts) >= 4:
            slug = parts[-1].replace("-", " ").strip()
            if slug:
                return slug
    except:
        pass

    return "(no title)"


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        if os.path.exists(SESSION_FILE):
            print("♻️ Using saved session")
            context = browser.new_context(storage_state=SESSION_FILE)
        else:
            context = browser.new_context()

        page = context.new_page()

        if os.path.exists(SESSION_FILE):
            if not is_logged_in(page):
                print("⚠️ Session expired, logging in again...")
                os.remove(SESSION_FILE)
                login(page, context)
        else:
            login(page, context)

        # Navigate to subreddit
        print("🌍 Opening subreddit...")
        page.goto(SUBREDDIT_URL)
        human_delay(3, 6)

        for _ in range(2):
            page.mouse.wheel(0, 2000)
            human_delay(2, 3)

        posts = page.locator("article")
        count = posts.count()
        print(f"📊 Found {count} posts")

        for i in range(min(count, 5)):
            try:
                post = posts.nth(i)

                title = get_post_title(post)
                print(f"\n📝 Post: {title}")

                if not is_lead(title):
                    print("⏭ Skipped (not a lead)")
                    continue

                print("🔥 Lead detected")

                post.locator("a[slot='full-post-link']").first.click()
                human_delay(3, 5)

                try:
                    full_text = page.locator("h1").inner_text()
                except:
                    full_text = title

                reply = "This is a generated reply."
                print("💬 Reply:", reply)

                comment_box = page.locator("div[contenteditable='true']").first
                comment_box.click()
                human_delay(1, 2)

                for char in reply:
                    page.keyboard.type(char)
                    time.sleep(random.uniform(0.02, 0.05))

                human_delay(2, 3)
                page.locator("button:has-text('Comment')").last.click()
                print("✅ Comment posted")

                human_delay(10, 15)
                page.go_back()
                human_delay(3, 5)

            except Exception as e:
                print(f"❌ Error on post {i}: {e}")
                try:
                    page.go_back()
                except:
                    pass
                human_delay(3, 5)

        browser.close()


if __name__ == "__main__":
    run()