"""Notification Service and Dispatcher."""

from typing import Optional, List
from sqlalchemy.orm import Session
from backend.repositories.notification_repo import NotificationRepository
from backend.models.notification import Notification, NotificationChannel
from backend.models.complaint import Complaint
from backend.utils.logging import logger


class NotificationService:
    """Dispatches notifications to citizens and officers."""

    def __init__(self, session: Session):
        self.session = session
        self.notif_repo = NotificationRepository(session)

    def notify_citizen_status_change(
        self,
        complaint: Complaint,
        new_status: str,
        remarks: Optional[str] = None,
    ) -> Notification:
        """Create citizen notification for status updates."""
        status_messages = {
            "SUBMITTED": ("Complaint Submitted", f"Your complaint {complaint.complaint_number} has been registered successfully."),
            "ACKNOWLEDGED": ("Complaint Acknowledged", f"The {complaint.department.name if complaint.department else 'responsible department'} has acknowledged your complaint {complaint.complaint_number}."),
            "ASSIGNED": ("Officer Assigned", f"An inspecting officer has been assigned to investigate {complaint.complaint_number}."),
            "IN_PROGRESS": ("Work In Progress", f"Remedial field work has started on your complaint {complaint.complaint_number}."),
            "WAITING_FOR_INFORMATION": ("Additional Details Requested", f"The officer has requested more details regarding {complaint.complaint_number}." + (f" Note: {remarks}" if remarks else "")),
            "RESOLVED": ("Complaint Resolved ✅", f"Your complaint {complaint.complaint_number} has been marked as Resolved." + (f" Resolution: {remarks}" if remarks else "")),
            "REJECTED": ("Complaint Update", f"Your complaint {complaint.complaint_number} could not be processed." + (f" Reason: {remarks}" if remarks else "")),
            "REOPENED": ("Complaint Reopened 🔄", f"Your complaint {complaint.complaint_number} has been reopened for further action."),
        }

        title, default_msg = status_messages.get(
            new_status,
            ("Status Updated", f"Status of complaint {complaint.complaint_number} changed to {new_status}."),
        )

        message = default_msg
        if remarks and new_status not in ["WAITING_FOR_INFORMATION", "RESOLVED", "REJECTED"]:
            message += f" Remarks: {remarks}"

        notif = self.notif_repo.create(
            user_id=complaint.citizen_id,
            complaint_id=complaint.id,
            title=title,
            message=message,
            channel=NotificationChannel.IN_APP.value,
        )

        logger.info(f"Citizen notification sent for {complaint.complaint_number}: {title}")
        return notif

    def notify_officer_assignment(self, officer_user_id: str, complaint: Complaint) -> Notification:
        """Notify assigned officer of new grievance in their queue."""
        notif = self.notif_repo.create(
            user_id=officer_user_id,
            complaint_id=complaint.id,
            title=f"New Task Assigned: {complaint.complaint_number}",
            message=f"You have been assigned to handle '{complaint.title}' ({complaint.severity} priority).",
            channel=NotificationChannel.IN_APP.value,
        )
        return notif

    def get_user_notifications(self, user_id: str) -> List[Notification]:
        """Fetch notifications for a user."""
        return self.notif_repo.list_for_user(user_id)

    def mark_as_read(self, notification_id: str) -> None:
        """Mark single notification as read."""
        self.notif_repo.mark_as_read(notification_id)

    def mark_all_read(self, user_id: str) -> None:
        """Mark all user notifications as read."""
        self.notif_repo.mark_all_read(user_id)
