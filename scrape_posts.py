from scraper import scrape_posts_reddit
from dotenv import load_dotenv
import os

load_dotenv()

reddit_client_id = os.environ.get("REDDIT_CLIENT_ID")
reddit_client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
reddit_user_agent = os.environ.get("REDDIT_USER_AGENT")

scrape_posts_reddit(
    subreddits = ["progmetal", "progrock", "djent", "metalcore", "epicmetal", "progrockmusic", "metal",
    "prog", "blackmetal", "deathcore", "postmetal", "doommetal", "sludge",
    "stonerrock", "rabm", "thrashmetal"],
    limit=3000,
    client_id=reddit_client_id,
    client_secret=reddit_client_secret,
    user_agent=reddit_user_agent
)