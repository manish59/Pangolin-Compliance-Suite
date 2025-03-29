from django.shortcuts import render
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, F, ExpressionWrapper, fields
from django.utils import timezone
from datetime import timedelta

from test_protocols.models import ProtocolRun, TestProtocol, TestSuite
from projects.models import Project


class DashboardView(LoginRequiredMixin, ListView):
    """
    View for the main dashboard that displays protocol runs statistics and recent activity
    """

    model = ProtocolRun
    template_name = "dashboard/dashboard.html"
    context_object_name = "protocol_runs"
    paginate_by = 10

    def get_queryset(self):
        """
        Get filtered protocol runs based on query parameters
        """
        queryset = ProtocolRun.objects.select_related(
            "protocol",
            "protocol__connection_config",
            "protocol__suite",
            "protocol__suite__project",
        ).order_by("-started_at")

        # Apply filters from query parameters
        project_id = self.request.GET.get("project")
        status = self.request.GET.get("status")
        result = self.request.GET.get("result")
        date_str = self.request.GET.get("date")

        if project_id:
            queryset = queryset.filter(protocol__suite__project_id=project_id)

        if status:
            queryset = queryset.filter(status=status)

        if result:
            queryset = queryset.filter(result_status=result)

        if date_str:
            try:
                # Filter runs that started on the specified date
                date_parts = date_str.split("-")
                year, month, day = (
                    int(date_parts[0]),
                    int(date_parts[1]),
                    int(date_parts[2]),
                )

                start_date = timezone.datetime(year, month, day)
                end_date = start_date + timedelta(days=1)

                # Convert to timezone-aware datetime if needed
                if timezone.is_naive(start_date):
                    start_date = timezone.make_aware(start_date)
                if timezone.is_naive(end_date):
                    end_date = timezone.make_aware(end_date)

                queryset = queryset.filter(
                    started_at__gte=start_date, started_at__lt=end_date
                )
            except (ValueError, IndexError):
                # Invalid date format, ignore the filter
                pass

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get statistics for summary cards
        context["total_runs"] = ProtocolRun.objects.count()
        context["running_protocols"] = ProtocolRun.objects.filter(
            status="running"
        ).count()
        context["failed_runs"] = ProtocolRun.objects.filter(
            Q(status="failed") | Q(result_status="fail")
        ).count()

        # Calculate success rate
        completed_runs = ProtocolRun.objects.filter(status="completed").count()
        if completed_runs > 0:
            success_runs = ProtocolRun.objects.filter(
                status="completed", result_status="pass"
            ).count()
            context["success_rate"] = round((success_runs / completed_runs) * 100)
        else:
            context["success_rate"] = 0

        # Get projects for filter dropdown
        context["projects"] = Project.objects.all()

        # Get recent activities
        # In a real implementation, this would be fetched from a dedicated activity log model
        # For now, we'll simulate it by getting recent runs with activity type
        recent_runs = ProtocolRun.objects.select_related("protocol").order_by(
            "-started_at"
        )[:10]

        activities = []
        for run in recent_runs:
            activity_type = "run_started"
            message = f"Protocol '{run.protocol.name}' run started"

            if run.status == "completed":
                activity_type = "run_completed"
                if run.result_status == "pass":
                    message = f"Protocol '{run.protocol.name}' completed successfully"
                else:
                    activity_type = "run_failed"
                    message = f"Protocol '{run.protocol.name}' failed with status: {run.result_status}"

            activities.append(
                {
                    "type": activity_type,
                    "message": message,
                    "timestamp": run.started_at,
                    "object": run,
                }
            )

        # Add some protocol creation activities for variety
        recent_protocols = TestProtocol.objects.select_related("suite").order_by(
            "-created_at"
        )[:5]
        for protocol in recent_protocols:
            activities.append(
                {
                    "type": "protocol_created",
                    "message": f"Protocol '{protocol.name}' created in suite '{protocol.suite.name}'",
                    "timestamp": protocol.created_at,
                    "object": protocol,
                }
            )

        # Sort activities by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        context["recent_activities"] = activities[:15]  # Limit to 15 activities

        return context
