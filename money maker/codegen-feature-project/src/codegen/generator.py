class CodeGenerator:
    def __init__(self, template_manager):
        self.template_manager = template_manager

    def generate_code(self, specifications):
        template = self.template_manager.get_template(specifications['template_name'])
        if not template:
            raise ValueError("Template not found.")
        
        code = template.format(**specifications['parameters'])
        return code

    def save_code(self, code, filename):
        with open(filename, 'w') as file:
            file.write(code)