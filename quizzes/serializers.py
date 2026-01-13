"""DRF serializers for quizzes app - PLACEHOLDER"""
from rest_framework import serializers
from .models import Category, Quiz, Question, QuizAttempt, Answer

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'color', 'emoji']

class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'difficulty', 'duration_minutes']

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'option_a', 'option_b', 'option_c', 'option_d', 'sequence']

class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ['id', 'status', 'correct_count', 'percentage_score', 'is_passed']

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'selected_answer', 'is_correct', 'time_spent_seconds']
