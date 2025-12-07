"""
Locust performance test file for EduRec system
Tests both Monolith and Microservices architecture
"""
from locust import HttpUser, task, between, SequentialTaskSet
import json
import random
import string

class EduRecUser(HttpUser):
    """
    Locust user class for testing EduRec system
    """
    wait_time = between(1, 3)  # Wait between 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a user starts"""
        self.user_id = None
        self.access_token = None
        self.user_email = f"test_user_{''.join(random.choices(string.ascii_lowercase, k=8))}@test.com"
        self.user_password = "test_password_123"
        
        # Register and login
        self.register()
        self.login()
    
    def refresh_token_if_needed(self):
        """Refresh token if it's expired or invalid"""
        # Try to login again to get a new token
        login_result = self.login()
        return login_result
    
    def register(self):
        """Register a new user"""
        register_data = {
            "email": self.user_email,
            "password": self.user_password,
            "full_name": "Test User",
            "school": "Test School",
            "current_grade": "10",
            "favorite_subjects": "Math, Physics",
            "learning_goals": "Improve grades",
            "preferred_learning_method": "Online"
        }
        
        with self.client.post("/auth/register", json=register_data, catch_response=True) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Registration failed: {response.status_code}")
    
    def login(self):
        """Login and get access token"""
        login_data = {
            "email": self.user_email,
            "password": self.user_password
        }
        
        with self.client.post("/auth/login", json=login_data, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.user_id = data.get("user_id")
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")
    
    @task(3)
    def get_health(self):
        """Check system health"""
        self.client.get("/health", name="Health Check")
    
    @task(5)
    def get_recommendations(self):
        """Get recommendations"""
        if not self.access_token:
            return
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        with self.client.post(
            "/recommendations/generate",
            json={
                "school": "Test School",
                "current_grade": "10",
                "favorite_subjects": "Math, Physics",
                "learning_goals": "Improve grades",
                "preferred_learning_method": "Online"
            },
            headers=headers,
            name="Generate Recommendations",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get recommendations: {response.status_code}")
    
    @task(4)
    def get_study_plan(self):
        """Get user's study plan"""
        if not self.user_id:
            return
        
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        
        with self.client.get(
            f"/study-plans/{self.user_id}",
            headers=headers,
            name="Get Study Plan",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:  # 404 is OK if no plan exists
                response.success()
            else:
                response.failure(f"Failed to get study plan: {response.status_code}")
    
    @task(2)
    def get_profile(self):
        """Get user profile"""
        if not self.user_id:
            return
        
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        
        with self.client.get(
            f"/profiles/{self.user_id}",
            headers=headers,
            name="Get Profile",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get profile: {response.status_code}")
    
    @task(2)
    def get_feedback(self):
        """Get user feedback"""
        if not self.user_id:
            return
        
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        
        with self.client.get(
            f"/feedback/{self.user_id}",
            headers=headers,
            name="Get Feedback",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:  # 404 is OK if no feedback
                response.success()
            else:
                response.failure(f"Failed to get feedback: {response.status_code}")
    
    @task(1)
    def get_catalog_courses(self):
        """Get catalog courses"""
        if not self.access_token:
            return
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        with self.client.get(
            "/catalog/courses",
            headers=headers,
            name="Get Catalog Courses",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                # Token might be expired, try to re-login and retry
                if self.login():
                    # Retry with new token
                    headers = {"Authorization": f"Bearer {self.access_token}"}
                    retry_response = self.client.get("/catalog/courses", headers=headers, name="Get Catalog Courses")
                    if retry_response.status_code == 200:
                        # Mark original response as success since retry worked
                        response.success()
                    else:
                        response.failure(f"Unauthorized (401) and retry failed ({retry_response.status_code})")
                else:
                    response.failure(f"Unauthorized (401): Token expired and re-login failed")
            elif response.status_code == 503:
                # Service unavailable, might be temporary
                response.failure(f"Service Unavailable (503): Catalog service may be down")
            elif response.status_code == 500:
                response.failure(f"Internal Server Error (500): {response.text[:100]}")
            else:
                try:
                    error_msg = response.json().get('error', response.text[:100])
                except:
                    error_msg = response.text[:100] if hasattr(response, 'text') else f"Status {response.status_code}"
                response.failure(f"Failed to get courses ({response.status_code}): {error_msg}")
    
    @task(1)
    def get_catalog_tutors(self):
        """Get catalog tutors"""
        if not self.access_token:
            return
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        with self.client.get(
            "/catalog/tutors",
            headers=headers,
            name="Get Catalog Tutors",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                # Token might be expired, try to re-login and retry
                if self.login():
                    # Retry with new token
                    headers = {"Authorization": f"Bearer {self.access_token}"}
                    retry_response = self.client.get("/catalog/tutors", headers=headers, name="Get Catalog Tutors")
                    if retry_response.status_code == 200:
                        # Mark original response as success since retry worked
                        response.success()
                    else:
                        response.failure(f"Unauthorized (401) and retry failed ({retry_response.status_code})")
                else:
                    response.failure(f"Unauthorized (401): Token expired and re-login failed")
            elif response.status_code == 503:
                # Service unavailable, might be temporary
                response.failure(f"Service Unavailable (503): Catalog service may be down")
            elif response.status_code == 500:
                response.failure(f"Internal Server Error (500): {response.text[:100]}")
            else:
                try:
                    error_msg = response.json().get('error', response.text[:100])
                except:
                    error_msg = response.text[:100] if hasattr(response, 'text') else f"Status {response.status_code}"
                response.failure(f"Failed to get tutors ({response.status_code}): {error_msg}")
    
    @task(1)
    def get_catalog_materials(self):
        """Get catalog materials"""
        if not self.access_token:
            return
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        with self.client.get(
            "/catalog/materials",
            headers=headers,
            name="Get Catalog Materials",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                # Token might be expired, try to re-login and retry
                if self.login():
                    # Retry with new token
                    headers = {"Authorization": f"Bearer {self.access_token}"}
                    retry_response = self.client.get("/catalog/materials", headers=headers, name="Get Catalog Materials")
                    if retry_response.status_code == 200:
                        # Mark original response as success since retry worked
                        response.success()
                    else:
                        response.failure(f"Unauthorized (401) and retry failed ({retry_response.status_code})")
                else:
                    response.failure(f"Unauthorized (401): Token expired and re-login failed")
            elif response.status_code == 503:
                # Service unavailable, might be temporary
                response.failure(f"Service Unavailable (503): Catalog service may be down")
            elif response.status_code == 500:
                response.failure(f"Internal Server Error (500): {response.text[:100]}")
            else:
                try:
                    error_msg = response.json().get('error', response.text[:100])
                except:
                    error_msg = response.text[:100] if hasattr(response, 'text') else f"Status {response.status_code}"
                response.failure(f"Failed to get materials ({response.status_code}): {error_msg}")


class AuthSequentialTaskSet(SequentialTaskSet):
    """Sequential tasks for authentication flow"""
    wait_time = between(1, 2)
    
    @task
    def test_auth_flow(self):
        """Test complete authentication flow"""
        # Register
        email = f"locust_{random.randint(1000, 9999)}@test.com"
        register_data = {
            "email": email,
            "password": "test123",
            "full_name": "Locust Test User"
        }
        
        self.client.post("/auth/register", json=register_data, name="Auth - Register")
        
        # Login
        login_data = {
            "email": email,
            "password": "test123"
        }
        response = self.client.post("/auth/login", json=login_data, name="Auth - Login")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            
            # Get profile with token
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                self.client.get("/auth/profile", headers=headers, name="Auth - Get Profile")


class StudyPlanTaskSet(SequentialTaskSet):
    """Sequential tasks for study plan operations"""
    wait_time = between(1, 2)
    
    def on_start(self):
        """Setup: Login first"""
        login_data = {
            "email": "test@example.com",
            "password": "test123"
        }
        response = self.client.post("/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.user_id = data.get("user_id")
        else:
            # Create test user
            register_data = {
                "email": "test@example.com",
                "password": "test123",
                "full_name": "Test User"
            }
            self.client.post("/auth/register", json=register_data)
            response = self.client.post("/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user_id")
    
    @task
    def test_study_plan_flow(self):
        """Test complete study plan flow"""
        if not self.token or not self.user_id:
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create study plan
        self.client.post(
            "/study-plans",
            json={"user_id": self.user_id},
            headers=headers,
            name="Study Plan - Create"
        )
        
        # Add item
        item_data = {
            "item_type": "course",
            "item_id": "1",
            "name": "Test Course",
            "subject": "Math",
            "grade": "10",
            "time_slots": "7h-9h thứ 3"
        }
        self.client.post(
            f"/study-plans/{self.user_id}/items",
            json=item_data,
            headers=headers,
            name="Study Plan - Add Item"
        )
        
        # Get study plan
        self.client.get(
            f"/study-plans/{self.user_id}",
            headers=headers,
            name="Study Plan - Get"
        )
        
        # Get schedule
        self.client.get(
            f"/study-plans/{self.user_id}/schedule",
            headers=headers,
            name="Study Plan - Get Schedule"
        )


class ApiGatewayUser(HttpUser):
    """User class for testing API Gateway specifically"""
    wait_time = between(1, 2)
    
    @task(10)
    def test_api_gateway_health(self):
        """Test API Gateway health endpoint"""
        self.client.get("/", name="API Gateway - Root")
    
    @task(5)
    def test_service_health(self):
        """Test service health checks"""
        self.client.get("/health", name="API Gateway - Health")


class RecommendationUser(HttpUser):
    """User class for testing recommendation service"""
    wait_time = between(2, 5)
    
    def on_start(self):
        """Setup: Login first"""
        # Initialize attributes to avoid AttributeError
        self.token = None
        self.user_id = None
        
        login_data = {
            "email": "recommendation_test@example.com",
            "password": "test123"
        }
        
        # Try to login, if fails, register
        response = self.client.post("/auth/login", json=login_data)
        if response.status_code != 200:
            register_data = {
                "email": "recommendation_test@example.com",
                "password": "test123",
                "full_name": "Recommendation Test User",
                "school": "Test School",
                "current_grade": "10",
                "favorite_subjects": "Math, Physics",
                "learning_goals": "Improve",
                "preferred_learning_method": "Online"
            }
            self.client.post("/auth/register", json=register_data)
            response = self.client.post("/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.user_id = data.get("user_id")
    
    @task(10)
    def generate_recommendations(self):
        """Generate recommendations"""
        if not self.token:
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        recommendation_data = {
            "school": "Test School",
            "current_grade": "10",
            "favorite_subjects": "Math, Physics",
            "learning_goals": "Improve grades",
            "preferred_learning_method": "Online"
        }
        
        with self.client.post(
            "/recommendations/generate",
            json=recommendation_data,
            headers=headers,
            name="Recommendation - Generate",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to generate recommendations: {response.status_code}")
    

