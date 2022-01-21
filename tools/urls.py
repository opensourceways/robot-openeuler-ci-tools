from django.urls import path
from tools.views import ReviewView


urlpatterns = [
    path('review/', ReviewView.as_view())
]
