from django.urls import path
from . import views

app_name = 'testsuite'

urlpatterns = [
    # TestSuite URLs
    path('', views.TestSuiteListView.as_view(), name='testsuite_list'),
    path('new/', views.TestSuiteCreateView.as_view(), name='testsuite_create'),
    path('<uuid:pk>/', views.TestSuiteDetailView.as_view(), name='testsuite_detail'),
    path('<uuid:pk>/edit/', views.TestSuiteUpdateView.as_view(), name='testsuite_update'),

    # TestProtocol URLs
    path('protocols/', views.TestProtocolListView.as_view(), name='protocol_list'),
    path('protocols/new/', views.TestProtocolCreateView.as_view(), name='protocol_create'),
    path('protocols/<uuid:pk>/', views.TestProtocolDetailView.as_view(), name='protocol_detail'),
    path('protocols/<uuid:pk>/edit/', views.TestProtocolUpdateView.as_view(), name='protocol_update'),
    path('suite/<uuid:suite_id>/protocols/new/', views.TestProtocolCreateFromSuiteView.as_view(),
         name='suite_protocol_create'),

    # ConnectionConfig URLs
    path('connections/', views.ConnectionConfigListView.as_view(), name='connection_list'),
    path('connections/new/', views.ConnectionConfigCreateView.as_view(), name='connection_create'),
    path('connections/<uuid:pk>/', views.ConnectionConfigDetailView.as_view(), name='connection_detail'),
    path('connections/<uuid:pk>/edit/', views.ConnectionConfigUpdateView.as_view(), name='connection_update'),
    path('protocols/<uuid:protocol_id>/connection/new/', views.ConnectionConfigCreateView.as_view(),
         name='protocol_connection_create'),

    # ProtocolRun URLs
    path('runs/', views.ProtocolRunListView.as_view(), name='run_list'),
    path('runs/<uuid:pk>/', views.ProtocolRunDetailView.as_view(), name='run_detail'),
    path('runs/new/', views.ProtocolRunCreateView.as_view(), name='run_create'),
    path('runs/<uuid:pk>/edit/', views.ProtocolRunUpdateView.as_view(), name='run_update'),
    path('protocols/<uuid:protocol_id>/runs/new/', views.ProtocolRunCreateView.as_view(), name='protocol_run_create'),

    # ProtocolResult URLs
    path('results/', views.ProtocolResultListView.as_view(), name='result_list'),
    path('results/<uuid:pk>/', views.ProtocolResultDetailView.as_view(), name='result_detail'),
    path('results/new/', views.ProtocolResultCreateView.as_view(), name='result_create'),
    path('results/<uuid:pk>/edit/', views.ProtocolResultUpdateView.as_view(), name='result_update'),
    path('runs/<uuid:run_id>/results/new/', views.ProtocolResultCreateView.as_view(), name='run_result_create'),

    # ResultAttachment URLs
    path('attachments/', views.ResultAttachmentListView.as_view(), name='attachment_list'),
    path('attachments/<uuid:pk>/', views.ResultAttachmentDetailView.as_view(), name='attachment_detail'),
    path('attachments/new/', views.ResultAttachmentCreateView.as_view(), name='attachment_create'),
    path('attachments/<uuid:pk>/edit/', views.ResultAttachmentUpdateView.as_view(), name='attachment_update'),
    path('results/<uuid:result_id>/attachments/new/', views.ResultAttachmentCreateView.as_view(),
         name='result_attachment_create'),

    # VerificationMethod URLs
    path('verifications/', views.VerificationMethodListView.as_view(), name='verification_list'),
    path('verifications/<uuid:pk>/', views.VerificationMethodDetailView.as_view(), name='verification_detail'),
    path('verifications/new/', views.VerificationMethodCreateView.as_view(), name='verification_create'),
    path('verifications/<uuid:pk>/edit/', views.VerificationMethodUpdateView.as_view(), name='verification_update'),
]