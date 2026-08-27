from locust import HttpUser, task, between
class PSBUser(HttpUser):
    wait_time=between(1,3)
    @task(3)
    def health(self): self.client.get("/health", name="health")
    @task(1)
    def verify(self): self.client.get("/verify/invalid-certificate", name="verify")
