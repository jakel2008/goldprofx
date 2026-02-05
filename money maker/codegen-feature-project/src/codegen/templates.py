class TemplateManager:
    def __init__(self):
        self.templates = {}

    def load_template(self, name, content):
        """Load a template with the given name and content."""
        self.templates[name] = content

    def get_template(self, name):
        """Retrieve the content of the template with the given name."""
        return self.templates.get(name, None)