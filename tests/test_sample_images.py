import http.client
import io
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
import server


def fixture(format="PNG", size=(64, 32)):
    output = io.BytesIO()
    image = Image.new("RGB", size, "#397257")
    image.save(output, format=format)
    return output.getvalue()


class SampleImageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.settings = patch.multiple(server, DATA_DIR=root, DB_PATH=root / "test.db",
                                       UPLOAD_DIR=root / "uploads", SESSIONS={})
        self.settings.start()
        server.initialize_database()
        with server.connect() as connection:
            users = connection.execute("SELECT user_id, role FROM app_user").fetchall()
            self.sample_id = connection.execute("SELECT MIN(sample_id) FROM coffee_sample").fetchone()[0]
        for user in users:
            server.SESSIONS[user["role"]] = {"user_id": user["user_id"], "expires_at": time.time() + 60}
        self.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.CoffeeAtlasHandler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.path = f"/api/samples/{self.sample_id}/image"

    def tearDown(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join()
        self.settings.stop()
        self.temp.cleanup()

    def request(self, method, path, body=None, role="admin", mime="image/png", headers=None):
        client = http.client.HTTPConnection("127.0.0.1", self.http.server_port, timeout=5)
        request_headers = {"Content-Type": mime}
        if role:
            request_headers["Cookie"] = f"{server.SESSION_COOKIE}={role}"
        request_headers.update(headers or {})
        client.request(method, path, body=body, headers=request_headers)
        response = client.getresponse()
        status, data, response_headers = response.status, response.read(), dict(response.getheaders())
        client.close()
        return status, data, response_headers

    def upload(self, body=None, mime="image/png"):
        status, data, _ = self.request("PUT", self.path, fixture() if body is None else body, mime=mime)
        self.assertEqual(status, 200, data)
        return json.loads(data)["imageUrl"]

    def test_admin_only_for_upload_and_remove(self):
        for method in ("PUT", "DELETE"):
            for role, expected in ((None, 401), ("user", 403)):
                self.assertEqual(self.request(method, self.path, fixture(), role=role)[0], expected)
        self.assertFalse(server.UPLOAD_DIR.exists())

    def test_formats_persistence_and_static_serving(self):
        for format, mime in (("PNG", "image/png"), ("JPEG", "image/jpeg"), ("WEBP", "image/webp")):
            url = self.upload(fixture(format), mime)
            status, data, headers = self.request("GET", url, role=None)
            self.assertEqual(status, 200)
            self.assertEqual(headers["Content-type"], "image/webp")
            self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
            with Image.open(io.BytesIO(data)) as image:
                self.assertEqual(image.format, "WEBP")
            with server.connect() as connection:
                bootstrap = server.serialize_bootstrap(connection)
                coffee = next(c for c in bootstrap["coffees"] if c["id"] == self.sample_id)
                self.assertEqual(coffee["imageUrl"], url)

    def test_replacement_and_removal_clean_up_files(self):
        first = self.upload()
        second = self.upload()
        self.assertFalse((server.UPLOAD_DIR / first.rsplit("/", 1)[1]).exists())
        self.assertTrue((server.UPLOAD_DIR / second.rsplit("/", 1)[1]).exists())
        self.assertEqual(self.request("DELETE", self.path)[0], 200)
        self.assertFalse(list(server.UPLOAD_DIR.iterdir()))
        with server.connect() as connection:
            self.assertEqual(connection.execute("SELECT image_url FROM coffee_sample WHERE sample_id = ?", (self.sample_id,)).fetchone()[0], "")

    def test_rejects_invalid_mismatched_large_and_missing_samples(self):
        for body, mime in ((b"bad image", "image/png"), (fixture(), "image/jpeg"), (b"<svg/>", "image/svg+xml"), (b"", "image/png")):
            self.assertEqual(self.request("PUT", self.path, body, mime=mime)[0], 400)
        self.assertEqual(self.request("PUT", self.path, b"", headers={"Content-Length": str(server.MAX_IMAGE_BYTES + 1)})[0], 413)
        self.assertEqual(self.request("PUT", "/api/samples/999999/image", fixture())[0], 404)
        self.assertEqual(self.request("DELETE", "/api/samples/999999/image")[0], 404)
        self.assertFalse(server.UPLOAD_DIR.exists())

    def test_resizes_images_and_removes_metadata(self):
        raw = io.BytesIO()
        image = Image.new("RGB", (2200, 1700), "green")
        exif = Image.Exif()
        exif[270] = "private test metadata"
        image.save(raw, format="JPEG", exif=exif)
        output = server.normalized_sample_image(raw.getvalue(), "image/jpeg")
        with Image.open(io.BytesIO(output)) as result:
            self.assertEqual(max(result.size), 1600)
            self.assertFalse(result.getexif())
        with patch.object(server, "MAX_IMAGE_PIXELS", 100):
            with self.assertRaises(ValueError):
                server.normalized_sample_image(fixture(), "image/png")

    def test_migration_is_additive_and_idempotent(self):
        with server.connect() as connection:
            before = connection.execute("SELECT sample_id, name, description FROM coffee_sample ORDER BY sample_id").fetchall()
            connection.execute("ALTER TABLE coffee_sample DROP COLUMN image_url")
        server.initialize_database()
        server.initialize_database()
        with server.connect() as connection:
            after = connection.execute("SELECT sample_id, name, description FROM coffee_sample ORDER BY sample_id").fetchall()
            self.assertEqual([tuple(row) for row in before], [tuple(row) for row in after])
            self.assertEqual(connection.execute("SELECT image_url FROM coffee_sample LIMIT 1").fetchone()[0], "")

    def test_sample_delete_removes_image_and_private_paths_are_not_served(self):
        url = self.upload()
        self.assertEqual(self.request("DELETE", f"/api/samples/{self.sample_id}")[0], 200)
        self.assertFalse((server.UPLOAD_DIR / url.rsplit("/", 1)[1]).exists())
        for path in ("/data/coffee_atlas.db", "/media/samples/../../test.db", "/media/samples/test.db"):
            self.assertEqual(self.request("GET", path, role=None)[0], 404)


if __name__ == "__main__":
    unittest.main()
