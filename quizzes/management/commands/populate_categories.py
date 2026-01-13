from django.core.management.base import BaseCommand
from quizzes.models import Category
import random

class Command(BaseCommand):
    help = 'Populates the database with initial quiz categories'

    def handle(self, *args, **kwargs):
        categories_list = [
            # Quantitative Aptitude
            "Percentages", "Ratio & Proportion", "Averages", "Profit & Loss", 
            "Simple Interest", "Compound Interest", "Time & Work", "Pipes & Cisterns", 
            "Time, Speed & Distance", "Problems on Trains", "Mixtures & Alligations", 
            "Partnership", "Number System", "HCF & LCM", "Simplification", 
            "Approximation", "Algebra (Linear Equations)", "Quadratic Equations", 
            "Permutations & Combinations", "Probability", "Mensuration – 2D", 
            "Mensuration – 3D", "Geometry Basics", "Coordinate Geometry", 
            "Set Theory", "Surds & Indices", "Logarithms", "Progressions (AP, GP, HP)", 
            "Inequalities", "Functions", "Venn Diagrams", "Bit Manipulation", "Mathematical Algorithms",
            
            # Data Interpretation
            "Data Interpretation – Tables", "Data Interpretation – Bar Graphs", 
            "Data Interpretation – Line Graphs", "Data Interpretation – Pie Charts", 
            "Caselet Data Interpretation", "Data Sufficiency",
            
            # Reasoning
            "Series Completion", "Word Problems", "Mathematical Reasoning", 
            
            # Computer Science / Programming
            "Introduction to Programming", "Variables & Data Types", "Operators", 
            "Input / Output", "Conditional Statements (if, switch)", 
            "Loops (for, while, do-while)", "Functions / Methods", "Recursion", 
            "Scope & Lifetime of Variables", "Type Casting", "Arrays", "Strings", 
            "Linked Lists", "Stacks", "Queues", "Hash Tables", "Trees", 
            "Binary Search Trees", "Heaps", "Graphs", "Searching Algorithms", 
            "Sorting Algorithms", "Greedy Algorithms", "Divide & Conquer", 
            "Dynamic Programming", "Backtracking", "Recursion-Based Algorithms", 
            "String Algorithms", 
            
            # Object Oriented Programming
            "Classes & Objects", "Encapsulation", "Inheritance", "Polymorphism", 
            "Abstraction", "Interfaces", "Constructors & Destructors", 
            
            # Advanced / System
            "Exception Handling", "File Handling", "Memory Management", 
            "Time & Space Complexity", "Debugging Techniques", "Version Control (Git)", 
            "Multithreading", "Concurrency", "Database Basics (SQL)", 
            "APIs & REST", "Testing (Unit Testing)", "Design Patterns", 
            "System Design Basics"
        ]

        # Colors for random assignment
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', 
                  '#D4A5A5', '#9B59B6', '#3498DB', '#E67E22', '#2ECC71']

        created_count = 0
        updated_count = 0

        for i, cat_name in enumerate(categories_list):
            # Assign order based on list index
            # Assign random color if creating new
            
            category, created = Category.objects.update_or_create(
                name=cat_name,
                defaults={
                    'order': i + 1,
                    # specific description could be added if available
                    'is_active': True
                }
            )
            
            # Only set color if created (preserve existing styling)
            if created:
                category.color = random.choice(colors)
                category.save()
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {cat_name}'))
            else:
                updated_count += 1
                self.stdout.write(f'Updated: {cat_name}')

        self.stdout.write(self.style.SUCCESS(f'Done! Created: {created_count}, Updated: {updated_count}'))
