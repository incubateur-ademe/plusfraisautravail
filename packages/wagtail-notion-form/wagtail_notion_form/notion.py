import logging
from dataclasses import dataclass

import requests
from django.utils import timezone

logger = logging.getLogger(__name__)

NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_VERSION = "2022-06-28"


@dataclass(frozen=True)
class ContactFormData:
    name: str
    email: str
    subject: str
    message: str


def create_new_row_in_notion_table(token: str, database_id: str, data: ContactFormData) -> bool:
    """Push a contact form submission to Notion as a new database row.

    Returns True on success. Never raises - failures are logged so a Notion
    outage can't break the contact form for site visitors.
    """
    if not token or not database_id:
        logger.error("Notion contact sync is not configured (missing token or database id)")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }
    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Nom": {"title": [{"text": {"content": data.name}}]},
            "Email": {"email": data.email},
            "Sujet": {"rich_text": [{"text": {"content": data.subject}}]},
            "Message": {"rich_text": [{"text": {"content": data.message}}]},
            "Date": {"date": {"start": timezone.now().isoformat()}},
        },
    }

    response = requests.post(NOTION_API_URL, headers=headers, json=payload, timeout=10)

    if response.status_code == 200:
        logger.info("Contact form submission synced to Notion")
        return True

    logger.error(
        "Failed to sync contact form to Notion: %s %s", response.status_code, response.text
    )
    return False
