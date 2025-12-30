import os
import sys

# Add ../lib to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from lib.message_model import BaseMessage

class BufferMessage(BaseMessage):
    """
    Extends BaseMessage to include social media specific fields like metrics and link attachments.
    """
    def __init__(self, id, date, status, content, metrics=None, link_attachment=None, **kwargs):
        super().__init__(id, date, status, content, **kwargs)
        self.metrics = metrics if metrics is not None else {}
        self.link_attachment = link_attachment

    def to_markdown(self, index, media_base_path=None):
        """Rozszerza standardowy Markdown o statystyki i załączniki linków."""
        base_md = super().to_markdown(index, media_base_path)
        lines = []
        
        if self.link_attachment:
            lines.append(f"\n### Link Attachment")
            lines.append(f"- **Title:** {self.link_attachment.get('title')}")
            lines.append(f"- **URL:** {self.link_attachment.get('url')}")
            if self.link_attachment.get('text'):
                lines.append(f"- **Description:** {self.link_attachment.get('text')}")

        if self.metrics:
            lines.append(f"\n### Engagement Metrics")
            for m_type, m_val in self.metrics.items():
                display_name = m_type.replace('Rate', ' Rate').title()
                unit = "%" if "Rate" in m_type else ""
                lines.append(f"- **{display_name}:** {m_val}{unit}")

        return base_md + "\n".join(lines) + "\n"

    @classmethod
    def from_dict(cls, data):
        return cls(**data)