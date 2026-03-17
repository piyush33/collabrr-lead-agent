import time
import os
from playwright.sync_api import sync_playwright
from llm import generate_reply
from filter import is_lead
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("REDDIT_USERNAME")
PASSWORD = os.getenv("REDDIT_PASSWORD")

SUBREDDIT_URL = "https://www.reddit.com/r/startups/new/"

def human_delay(min_s=2, max_s=5):
    import random
    time.sleep(random.uniform(min_s, max_s))


def run():

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 🔐 Login
        page.goto("https://www.reddit.com/login/")
        human_delay()

        page.fill("input[name='username']", USERNAME)
        page.fill("input[name='password']", PASSWORD)

        page.click("button[type='submit']")
        human_delay(5, 8)

        # 🌍 Go to subreddit
        page.goto(SUBREDDIT_URL)
        human_delay()

        posts = page.locator("div[data-testid='post-container']").all()

        print(f"Found {len(posts)} posts")

        for post in posts[:5]:  # limit for safety

            try:
                title = post.locator("h3").inner_text()
                print("Post:", title)

                if not is_lead(title):
                    continue

                print("Lead detected")

                post.click()
                human_delay()

                full_text = page.locator("h1").inner_text()

                reply = generate_reply(full_text)
                print("Reply:", reply)

                # ✍️ Click comment box
                page.click("div[role='textbox']")
                human_delay()

                page.keyboard.type(reply, delay=50)

                human_delay()

                # 🚀 Submit
                page.click("button:has-text('Comment')")

                print("Comment posted")

                human_delay(10, 15)

                page.go_back()
                human_delay()

            except Exception as e:
                print("Error:", e)
                page.go_back()

        browser.close()


if __name__ == "__main__":
    run()