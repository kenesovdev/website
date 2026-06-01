from django.urls import path

from .views import SubmissionDetailView, SubmissionListView, TestRunView

urlpatterns = [
    path('submissions/test/', TestRunView.as_view(), name='submissions-test-run'),
    path('submissions/<int:pk>/', SubmissionDetailView.as_view(), name='submission-detail'),
    path('submissions/', SubmissionListView.as_view(), name='submission-list'),
]
