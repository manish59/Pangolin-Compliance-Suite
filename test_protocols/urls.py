from django.urls import path
from . import views

app_name = "testsuite"

urlpatterns = [
    # TestSuite URLs
    path("", views.TestSuiteListView.as_view(), name="testsuite_list"),
    path("new/", views.TestSuiteCreateView.as_view(), name="testsuite_create"),
    path("<uuid:pk>/", views.TestSuiteDetailView.as_view(), name="testsuite_detail"),
    path(
        "<uuid:pk>/edit/", views.TestSuiteUpdateView.as_view(), name="testsuite_update"
    ),
    path("<uuid:pk>/run/", views.RunTestSuiteView.as_view(), name="testsuite_run"),
    # TestProtocol URLs
    path("protocols/", views.TestProtocolListView.as_view(), name="protocol_list"),
    path(
        "protocols/new/", views.TestProtocolCreateView.as_view(), name="protocol_create"
    ),
    path(
        "protocols/<uuid:pk>/",
        views.TestProtocolDetailView.as_view(),
        name="protocol_detail",
    ),
    path(
        "protocols/<uuid:pk>/edit/",
        views.TestProtocolUpdateView.as_view(),
        name="protocol_update",
    ),
    path(
        "suite/<uuid:suite_id>/protocols/new/",
        views.TestProtocolCreateFromSuiteView.as_view(),
        name="suite_protocol_create",
    ),
    # ConnectionConfig URLs
    path(
        "connections/", views.ConnectionConfigListView.as_view(), name="connection_list"
    ),
    path(
        "connections/new/",
        views.ConnectionConfigCreateView.as_view(),
        name="connection_create",
    ),
    path(
        "connections/<uuid:pk>/",
        views.ConnectionConfigDetailView.as_view(),
        name="connection_detail",
    ),
    path(
        "connections/<uuid:pk>/edit/",
        views.ConnectionConfigUpdateView.as_view(),
        name="connection_update",
    ),
    path(
        "protocols/<uuid:protocol_id>/connection/new/",
        views.ConnectionConfigCreateView.as_view(),
        name="protocol_connection_create",
    ),
    # ProtocolRun URLs
    path("runs/", views.ProtocolRunListView.as_view(), name="run_list"),
    path("runs/<uuid:pk>/", views.ProtocolRunDetailView.as_view(), name="run_detail"),
    path("runs/new/", views.ProtocolRunCreateView.as_view(), name="run_create"),
    path(
        "runs/<uuid:pk>/edit/", views.ProtocolRunUpdateView.as_view(), name="run_update"
    ),
    path(
        "protocols/<uuid:protocol_id>/runs/new/",
        views.ProtocolRunCreateView.as_view(),
        name="protocol_run_create",
    ),
    # VerificationMethod URLs
    path(
        "verifications/",
        views.VerificationMethodListView.as_view(),
        name="verification_list",
    ),
    path(
        "verifications/<uuid:pk>/",
        views.VerificationMethodDetailView.as_view(),
        name="verification_detail",
    ),
    path(
        "verifications/new/",
        views.VerificationMethodCreateView.as_view(),
        name="verification_create",
    ),
    path(
        "verifications/<uuid:pk>/edit/",
        views.VerificationMethodUpdateView.as_view(),
        name="verification_update",
    ),
    # List execution steps for a specific protocol
    path(
        "protocol/<uuid:protocol_id>/steps/",
        views.ExecutionStepListView.as_view(),
        name="step_list",
    ),
    # Create a new execution step for a protocol
    path(
        "protocol/<uuid:protocol_id>/steps/create/",
        views.ExecutionStepCreateView.as_view(),
        name="protocol_step_create",
    ),
    # View details of a specific execution step
    path(
        "steps/<uuid:pk>/", views.ExecutionStepDetailView.as_view(), name="step_detail"
    ),
    # Update an execution step
    path(
        "steps/<uuid:pk>/update/",
        views.ExecutionStepUpdateView.as_view(),
        name="step_update",
    ),
    # Delete an execution step
    path(
        "steps/<uuid:pk>/delete/",
        views.ExecutionStepDeleteView.as_view(),
        name="step_delete",
    ),
    # Reorder steps for a protocol
    path(
        "protocol/<uuid:protocol_id>/steps/reorder/",
        views.ExecutionStepReorderView.as_view(),
        name="step_reorder",
    ),
    # Clone an execution step
    path(
        "steps/<uuid:pk>/clone/",
        views.ExecutionStepCloneView.as_view(),
        name="step_clone",
    ),
    # View execution step results in a run
    path(
        "runs/<uuid:run_id>/steps/",
        views.RunExecutionStepsView.as_view(),
        name="run_steps",
    ),
    # Execute a specific step during a protocol run
    path(
        "runs/<uuid:run_id>/steps/<uuid:step_id>/execute/",
        views.ExecuteStepView.as_view(),
        name="execute_step",
    ),
    # New URLs for protocol-specific verification methods
    path(
        "protocols/<uuid:protocol_id>/verification/create/",
        views.ProtocolVerificationCreateView.as_view(),
        name="protocol_verification_create",
    ),
    path(
        "protocols/<uuid:protocol_id>/verification/<uuid:pk>/",
        views.ProtocolVerificationDetailView.as_view(),
        name="protocol_verification_detail",
    ),
    path(
        "protocols/<uuid:protocol_id>/verification/<uuid:pk>/edit/",
        views.ProtocolVerificationUpdateView.as_view(),
        name="protocol_verification_edit",
    ),
    path(
        "protocols/<uuid:protocol_id>/verification/<uuid:pk>/delete/",
        views.ProtocolVerificationDeleteView.as_view(),
        name="protocol_verification_delete",
    ),
    path(
        "protocols/<uuid:protocol_id>/verifications/",
        views.ProtocolVerificationListView.as_view(),
        name="protocol_verification_list",
    ),
]
