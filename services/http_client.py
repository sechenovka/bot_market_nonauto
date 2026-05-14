import aiohttp

def get_session():
    """Временно без прокси."""
    return aiohttp.ClientSession()