import logging

logger = logging.getLogger(__name__)

class MockYoutubeDL:
    def __init__(self, opts):
        self.opts = opts
        logger.info("DummyYoutubeDL created with opts: %s", opts)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def download(self, urls):
        logger.info("Simulated download for urls: %s", urls)

    def extract_info(self, url, download=False):
        logger.info("Simulated extract_info for url: %s", url)

        if url.startswith("ytsearch:"):
            query = url[len("ytsearch:"):]
            return {
                "entries": [
                    {
                        "title": f"Dummy Title for {query}",
                        "webpage_url": f"http://dummy.url/{query.replace(' ', '_')}"
                    }
                ]
            }

        return {"title": "Dummy Title", "webpage_url": url}