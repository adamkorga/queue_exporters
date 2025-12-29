import json

class BaseMessage:
    def __init__(self, id, date, status, content, subject=None, preview=None, 
                 media=None, source=None, subchannel=None):
        self.id = str(id)
        self.date = date
        self.status = status.lower()
        self.content = content
        self.subject = subject
        self.preview = preview
        self.media = media if media is not None else []
        self.source = source
        self.subchannel = subchannel

    def to_dict(self):
        """Konwertuje obiekt na słownik do zapisu w JSON."""
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        """Tworzy obiekt klasy na podstawie słownika z JSON."""
        return cls(**data)

    def to_markdown(self, index, media_base_path=None):
        """Generuje fragment Markdown dla tej konkretnej wiadomości."""
        lines = [
            "---",
            f"## {index}. {self.subject or f'Post {self.date}'}",
            f"- **Date:** {self.date}",
            f"- **Status:** {self.status.upper()}",
        ]
        
        if self.source:
            source_str = f"{self.source}"
            if self.subchannel:
                source_str += f" ({self.subchannel})"
            lines.append(f"- **Source:** {source_str}")
            
        if self.preview:
            lines.append(f"- **Preview:** *{self.preview}*")
            
        lines.append(f"\n### Content\n\n{self.content}\n")
        
        if self.media:
            lines.append("\n### Media")
            for item in self.media:
                if item['type'] == 'image':
                    url = item['url']
                    # Logika relatywnej ścieżki przeniesiona tutaj
                    if media_base_path and url.startswith(media_base_path):
                        import os
                        url = os.path.join("media", os.path.basename(url))
                    lines.append(f"![{item.get('alt', 'image')}]({url})")
                elif item['type'] == 'link':
                    lines.append(f"- [External Link]({item['url']})")
        
        return "\n".join(lines) + "\n"