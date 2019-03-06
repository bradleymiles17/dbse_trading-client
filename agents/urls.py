from django.urls import path

from . import views

app_name = 'agents'
urlpatterns = [
    path('', views.index, name='index'),
    path('agents/giveaway', views.giveaway, name='agent'),
    path('agents/shaver', views.shaver, name='shaver')
]