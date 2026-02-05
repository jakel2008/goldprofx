class DeveloperInterface:
    def __init__(self):
        self.title = "Code Generation Interface"

    def show_interface(self):
        print(f"{self.title}\n{'=' * len(self.title)}")
        print("Welcome to the Code Generation Tool!")
        print("Please provide the specifications for the code you want to generate.")

    def get_user_input(self):
        specifications = input("Enter your code specifications: ")
        return specifications

    def display_generated_code(self, code):
        print("\nGenerated Code:\n")
        print(code)