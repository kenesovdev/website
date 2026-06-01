from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.submissions.models import Submission
from apps.problems.models import Problem
from apps.users.jwt_utils import generate_access_token

User = get_user_model()


class SubmissionAPITestCase(APITestCase):
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(
            email="user1@example.com", handle="user1", password="password"
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com", handle="user2", password="password"
        )
        
        # Create problems
        self.problem1 = Problem.objects.create(
            title="Two Sum", statement="Solve two sum"
        )
        self.problem2 = Problem.objects.create(
            title="Add Two Numbers", statement="Add two numbers"
        )

        # Create submissions for user1
        self.sub_u1_p1 = Submission.objects.create(
            user=self.user1,
            problem=self.problem1,
            code="print(user1_p1)",
            language="python",
            status="done",
            verdict="AC",
            time_ms=100,
            memory_kb=2048
        )
        self.sub_u1_p2 = Submission.objects.create(
            user=self.user1,
            problem=self.problem2,
            code="print(user1_p2)",
            language="python",
            status="done",
            verdict="WA",
            time_ms=200,
            memory_kb=4096
        )

        # Create submission for user2
        self.sub_u2_p1 = Submission.objects.create(
            user=self.user2,
            problem=self.problem1,
            code="print(user2_p1)",
            language="python",
            status="done",
            verdict="AC",
            time_ms=150,
            memory_kb=1024
        )

        # Bypass the celery tasks side-effect in tests setup by resetting status in db
        Submission.objects.filter(user=self.user1).update(status='done')
        Submission.objects.filter(user=self.user2).update(status='done')

        # Generate tokens
        self.token1 = generate_access_token(self.user1)
        self.token2 = generate_access_token(self.user2)

    def test_list_returns_only_current_users_submissions(self):
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        
        url = reverse('submission-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return exactly 2 submissions belonging to user1
        self.assertEqual(response.data['count'], 2)
        
        # Verify user2's submission is NOT in the results
        results = response.data['results']
        retrieved_ids = {item['id'] for item in results}
        self.assertIn(self.sub_u1_p1.id, retrieved_ids)
        self.assertIn(self.sub_u1_p2.id, retrieved_ids)
        self.assertNotIn(self.sub_u2_p1.id, retrieved_ids)

    def test_filter_by_problem_id_works(self):
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        
        url = reverse('submission-list')
        # Filter by problem1 id
        response = self.client.get(url, {'problem': self.problem1.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.sub_u1_p1.id)

        # Filter by problem2 slug
        response = self.client.get(url, {'problem_slug': self.problem2.slug})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.sub_u1_p2.id)

        # Filter by status
        response = self.client.get(url, {'status': 'done'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_detail_returns_code_list_does_not(self):
        # Authenticate as user1
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        
        # 1. Check detail endpoint has code
        url_detail = reverse('submission-detail', kwargs={'pk': self.sub_u1_p1.id})
        response_detail = self.client.get(url_detail)
        
        self.assertEqual(response_detail.status_code, status.HTTP_200_OK)
        self.assertIn('code', response_detail.data)
        self.assertEqual(response_detail.data['code'], "print(user1_p1)")

        # 2. Check list endpoint does NOT have code
        url_list = reverse('submission-list')
        response_list = self.client.get(url_list)
        
        self.assertEqual(response_list.status_code, status.HTTP_200_OK)
        for result in response_list.data['results']:
            self.assertNotIn('code', result)
