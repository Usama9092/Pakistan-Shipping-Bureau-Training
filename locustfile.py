"""Non-mutating public load plan for a Streamlit PSB deployment."""
from locust import HttpUser, task, between


class PSBUser(HttpUser):
    wait_time = between(1, 3)

    @task(4)
    def health(self):
        self.client.get("/_stcore/health", name="streamlit-health")

    @task(2)
    def host_config(self):
        self.client.get("/_stcore/host-config", name="streamlit-host-config")

    @task(1)
    def login_shell(self):
        self.client.get("/", name="login-shell")

