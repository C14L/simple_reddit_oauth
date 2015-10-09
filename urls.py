from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'login/', views.login_view),
    url(r'redditcallback/', views.reddit_callback_view),
    url(r'logout/', views.logout_view),
]
