from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('list-management/', views.list_management, name='list_management'),
    path('records-variations/', views.records_variations, name='records_variations'),
    path('view-variations/', views.view_variations, name='view_variations'),
    path('all-variations/', views.all_variations, name='all_variations'),
    path('generate-test-data/', views.generate_test_data, name='generate_test_data'),
    path('record/<int:record_id>/', views.view_record, name='view_record'),
    path('edit-variation/<int:variation_id>/', views.edit_variation, name='edit_variation'),
    


]
