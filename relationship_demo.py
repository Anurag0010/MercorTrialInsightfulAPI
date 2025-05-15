from app import create_app, db
from api.models import Employee, Project, Task

def demonstrate_relationships():
    # Create the app context
    app = create_app()
    
    with app.app_context():
        # Clear existing data
        db.session.query(Employee).delete()
        db.session.query(Project).delete()
        db.session.query(Task).delete()
        
        # Create an employee
        john = Employee(name='John Doe', email='john@example.com')
        
        # Create a project
        web_project = Project(name='Web Application Project')
        mobile_project = Project(name='Mobile App Project')
        
        # Add the employee to a project
        web_project.employees.append(john)
        
        # Add the project to the employee (this is the magic of back_populates)
        # Note: This is redundant but demonstrates the bidirectional nature
        # john.projects.append(web_project)
        
        # Create a task and associate with the employee and project
        task = Task(
            name='Implement Login',
            project=web_project,
            description='Create login functionality'
        )
        task.employees.append(john)
        
        # Save to database
        db.session.add(john)
        db.session.add(web_project)
        db.session.add(mobile_project)
        db.session.add(task)
        db.session.commit()
        
        # Demonstrate the relationships
        print("John's Projects:")
        for project in john.projects:
            print(f"- {project.name}")
        
        print("\nWeb Project's Employees:")
        for employee in web_project.employees:
            print(f"- {employee.name}")
        
        print("\nJohn's Tasks:")
        for task in john.tasks:
            print(f"- {task.name} (Project: {task.project.name})")

if __name__ == '__main__':
    demonstrate_relationships()
