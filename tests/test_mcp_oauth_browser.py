"""Optional browser regression: pip install playwright; requires local Edge."""
import unittest
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

import test_mcp_oauth


@unittest.skipUnless(sync_playwright, "Install playwright to run browser regression")
class ConsentBrowserTests(unittest.TestCase):
    def test_external_callback_after_first_click(self):
        fixture = test_mcp_oauth.OAuthTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.client.cookies.set("login", "yes")
        legacy = [True]
        callbacks = []
        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                callbacks.append(self.path)
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Callback received</h1>")

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), CallbackHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        origin = f"http://127.0.0.1:{server.server_port}"
        fixture.callback = origin + "/callback"
        registered = fixture.client.post("/register", json={"redirect_uris": [fixture.callback],
            "token_endpoint_auth_method": "client_secret_post", "scope": "mcp"}).json()
        fixture.credentials = {key: registered[key] for key in ("client_id", "client_secret")}
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page()
            console = []
            page.on("console", lambda message: console.append(message.text))

            def handle(route):
                req = route.request
                parsed = urlsplit(req.url)
                response = fixture.client.request(req.method, parsed.path + "?" + parsed.query,
                    content=req.post_data, headers=req.headers)
                headers = dict(response.headers)
                if legacy[0] and "content-security-policy" in headers:
                    headers["content-security-policy"] = headers["content-security-policy"].replace(
                        f"form-action 'self' {origin};", "form-action 'self';")
                route.fulfill(status=response.status_code, headers=headers, body=response.content)

            page.route("http://localhost/**", handle)
            page.context.add_cookies([{"name": "login", "value": "yes", "url": "http://localhost"}])
            old_location = fixture.authorize().headers["location"]
            page.goto(old_location)
            page.get_by_role("button", name="Autorizar", exact=True).click()
            page.wait_for_timeout(500)
            self.assertFalse(callbacks)
            self.assertTrue(any("form-action" in message for message in console), console)
            ticket = parse_qs(urlsplit(old_location).query)["ticket"][0]
            self.assertIsNone(fixture.provider.store.get("pending", ticket))

            legacy[0] = False
            page.goto(fixture.authorize().headers["location"])
            page.get_by_role("button", name="Autorizar", exact=True).click()
            page.wait_for_url(origin + "/callback?**")
            self.assertEqual(len(callbacks), 1)
            params = parse_qs(urlsplit(callbacks[0]).query)
            self.assertEqual(params.get("state"), ["original-state"], callbacks)
            self.assertEqual(fixture.exchange(params["code"][0]).status_code, 200)
            browser.close()


if __name__ == "__main__":
    unittest.main()
