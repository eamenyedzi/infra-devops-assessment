from locust import HttpUser, task, between

class StaticSiteUser(HttpUser):
    wait_time = between(1, 2)

    @task(2)
    def get_page1(self):
        self.client.get("/1")

    @task(1)
    def get_page2(self):
        self.client.get("/2")