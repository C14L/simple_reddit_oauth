from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'login/', views.login_view, name='logout_page'),
    url(r'redditcallback/', views.reddit_callback_view, name='redditcb_page'),
    url(r'logout/', views.logout_view, name='logout_page'),
]
