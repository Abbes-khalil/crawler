from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx


class RobotsPolicy:
    """Wraps a parsed robots.txt for one domain. If robots.txt could not
    be fetched or parsed, everything is allowed (fail-open), matching
    normal crawler etiquette - a missing robots.txt is not a denial."""

    def __init__(
        self,
        parser: RobotFileParser | None,
        sitemap_urls: list[str],
    ):
        self._parser = parser
        self.sitemap_urls = sitemap_urls

    def is_allowed(self, url: str, user_agent: str) -> bool:
        if self._parser is None:
            return True

        return self._parser.can_fetch(user_agent, url)


async def fetch_robots_policy(
    homepage_url: str,
    client: httpx.AsyncClient,
) -> RobotsPolicy:
    parsed = urlparse(homepage_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    try:
        response = await client.get(robots_url)
    except httpx.HTTPError:
        return RobotsPolicy(parser=None, sitemap_urls=[])

    if response.status_code >= 400:
        return RobotsPolicy(parser=None, sitemap_urls=[])

    parser = RobotFileParser()
    parser.parse(response.text.splitlines())

    sitemap_urls = list(parser.site_maps() or [])

    return RobotsPolicy(parser=parser, sitemap_urls=sitemap_urls)
