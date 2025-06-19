"""Locust load test script simulating authentication requests.

Run with: locust -f backend/locustfile.py --headless -u 50 -r 10 -t 30s

This is a smoke profile suitable for CI; full-scale load tests should be
executed in dedicated performance pipelines.
"""

from locust import HttpUser, between, task


class AuthUser(HttpUser):
    host = "http://localhost:8000"
    wait_time = between(0.5, 1.5)

    username = "perf_user@example.com"
    password = "PerfUserPassw0rd!"

    def on_start(self):
        """Ensure the performance test user exists by attempting registration once."""

        # Attempt to register the test user; ignore 409 Conflict if it already exists
        with self.client.post(
            "/auth/register",
            json={
                "username": self.username,
                "email": self.username,
                "password": self.password,
            },
            timeout=10,
            catch_response=True,
        ) as resp:
            if resp.status_code in (201, 409):
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}: {resp.text[:120]}")

    @task
    def obtain_token(self):
        """Hit the /auth/token endpoint to obtain a JWT."""

        with self.client.post(
            "/auth/token",
            data={"username": self.username, "password": self.password},
            timeout=10,
            catch_response=True,
        ) as response:
            if response.status_code in (200, 429):
                response.success()
            else:
                response.failure(
                    f"Unexpected status {response.status_code}: {response.text[:120]}"
                )
