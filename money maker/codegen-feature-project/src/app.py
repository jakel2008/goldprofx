from codegen.generator import CodeGenerator
from ui.developer_interface import DeveloperInterface

def main():
    # Initialize the code generator
    code_generator = CodeGenerator()
    
    # Initialize the developer interface
    developer_interface = DeveloperInterface()

    # Show the interface to the user
    developer_interface.show_interface()

    # Get user input for code generation
    specifications = developer_interface.get_user_input()

    # Generate code based on user specifications
    generated_code = code_generator.generate_code(specifications)

    # Save the generated code
    code_generator.save_code(generated_code)

if __name__ == "__main__":
    main()