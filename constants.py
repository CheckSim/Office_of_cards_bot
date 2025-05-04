spotify_url = 'https://api.spotify.com/v1/shows/2cqzDBQRxqgba39VPp3FDs/episodes?market=IT'
spotify_url_pills = 'https://api.spotify.com/v1/shows/5ILsIKO18lp9aemJqcAWdb/episodes?market=IT'

apple_url = 'https://podcasts.apple.com/gb/podcast/made-it-storie-di-start-up-innovative/id1518862081'

google_podcast_url = 'https://podcasts.google.com/feed/aHR0cHM6Ly9mZWVkcy5tZWdhcGhvbmUuZm0vb2ZmaWNlb2ZjYXJkcw?sa=X&ved=2ahUKEwiX24SBqLv9AhX2gv0HHVi4AcAQ9sEGegQIARAG'
google_podcast_url_pills = 'https://podcasts.google.com/feed/aHR0cHM6Ly9mZWVkcy5tZWdhcGhvbmUuZm0vTU5USEE2MTAwOTQzOTIx?sa=X&ved=0CAcQrrcFahcKEwiY4pX7-bP-AhUAAAAAHQAAAAAQLA'

import os
from dotenv import load_dotenv, find_dotenv

# these expect to find a .env file at the directory above the lesson.                                                                                                                     # the format for that file is (without the comment)                                                                                                                                       #API_KEYNAME=AStringThatIsTheLongAPIKeyFromSomeService
def load_env():
    _ = load_dotenv(find_dotenv())

def get_bot_token():
    load_env()
    bot_token = os.getenv("BOT_TOKEN")
    return bot_token

def get_spotify_credentials():
    load_env()
    spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
    spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    return spotify_client_id, spotify_client_secret