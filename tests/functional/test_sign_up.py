from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from monchat_server.models import MonchatUser
from monchat_server.utils import generate_id, hash_password
from unittest.mock import patch


class SignupViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse("signup")

    def test_successful_signup(self):
        data = {
            "fname": "John",
            "lname": "Doe",
            "uname": "johndoe",
            "pwd": "strongpassword",
        }
        response = self.client.post(self.signup_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["msg"], "Signed up successfully!")
        self.assertTrue("data" in response.data)

    def test_missing_data(self):
        data = {"lname": "Doe", "uname": "johndoe", "pwd": "strongpassword"}
        response = self.client.post(self.signup_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["msg"], "Invalid request data")

    def test_existing_username(self):
        data = {
            "fname": "John",
            "lname": "Doe",
            "uname": "existinguser",
            "pwd": "strongpassword",
        }
        # create a user with the same username
        MonchatUser.objects.create(
            first_name="Jane",
            last_name="Doe",
            user_name="existinguser",
            user_id=generate_id(prefix="user"),
            user_icon="user.svg",
            password=hash_password("strongpassword"),
        )
        response = self.client.post(self.signup_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["msg"], "Username already exists")

    def test_invalid_password(self):
        data = {"fname": "John", "lname": "Doe", "uname": "johndoe", "pwd": "weak"}
        response = self.client.post(self.signup_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["msg"], "Weak password")
