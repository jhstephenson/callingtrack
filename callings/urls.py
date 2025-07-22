from django.urls import path
from . import views

app_name = 'callings'

urlpatterns = [
    # Dashboard is handled in the main urls.py
    
    # Unit URLs
    path('units/', views.UnitListView.as_view(), name='unit-list'),
    path('units/<int:pk>/', views.UnitDetailView.as_view(), name='unit-detail'),
    path('units/create/', views.UnitCreateView.as_view(), name='unit-create'),
    path('units/<int:pk>/update/', views.UnitUpdateView.as_view(), name='unit-update'),
    path('units/<int:pk>/delete/', views.UnitDeleteView.as_view(), name='unit-delete'),
    
    # Organization URLs
    path('organizations/', views.OrganizationListView.as_view(), name='organization-list'),
    path('organizations/<int:pk>/', views.OrganizationDetailView.as_view(), name='organization-detail'),
    path('organizations/create/', views.OrganizationCreateView.as_view(), name='organization-create'),
    path('organizations/<int:pk>/update/', views.OrganizationUpdateView.as_view(), name='organization-update'),
    path('organizations/<int:pk>/delete/', views.OrganizationDeleteView.as_view(), name='organization-delete'),
    
    # Position URLs
    path('positions/', views.PositionListView.as_view(), name='position-list'),
    path('positions/<int:pk>/', views.PositionDetailView.as_view(), name='position-detail'),
    path('positions/create/', views.PositionCreateView.as_view(), name='position-create'),
    path('positions/<int:pk>/update/', views.PositionUpdateView.as_view(), name='position-update'),
    path('positions/<int:pk>/delete/', views.PositionDeleteView.as_view(), name='position-delete'),
    
    # Calling URLs
    path('callings/', views.CallingListView.as_view(), name='calling-list'),
    path('callings/by-unit/', views.CallingsByUnitView.as_view(), name='callings-by-unit'),
    path('callings/<int:pk>/', views.CallingDetailView.as_view(), name='calling-detail'),
    path('callings/create/', views.CallingCreateView.as_view(), name='calling-create'),
    path('callings/<int:pk>/update/', views.CallingUpdateView.as_view(), name='calling-update'),
    path('callings/<int:pk>/delete/', views.CallingDeleteView.as_view(), name='calling-delete'),
    path('callings/<int:pk>/release/', views.CallingReleaseView.as_view(), name='calling-release'),
    path('callings/<int:pk>/lcr-update/', views.CallingLCRUpdateView.as_view(), name='calling-lcr-update'),
    path('callings/<int:pk>/update-status/<str:new_status>/', views.CallingUpdateStatusView.as_view(), name='calling-update-status'),
    
    # Documentation URLs
    path('docs/user-guide/', views.UserGuideView.as_view(), name='user-guide'),
    path('docs/admin-guide/', views.AdminGuideView.as_view(), name='admin-guide'),
    path('docs/technical-guide/', views.TechnicalGuideView.as_view(), name='technical-guide'),
]
