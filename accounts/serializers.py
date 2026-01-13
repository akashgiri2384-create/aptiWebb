from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, UserProfile, College, OTPVerification
from .otp_utils import OTPManager

# --- Original Serializers (Reconstructed) ---

class CollegeSerializer(serializers.ModelSerializer):
    class Meta:
        model = College
        fields = ['id', 'name', 'code', 'city', 'state']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'full_name', 'college', 'year', 'branch', 'roll_number', 'mobile_number']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    season_xp = serializers.SerializerMethodField()
    rank_badge = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'avatar', 'bio', 'theme', 'total_xp', 'current_rank', 'accuracy_percentage', 'practice_streak', 'season_xp', 'rank_badge']
        read_only_fields = ['total_xp', 'current_rank', 'accuracy_percentage', 'practice_streak']

    def get_season_xp(self, obj):
        try:
            return obj.user.xp_stats.season_xp
        except:
            return 0
            
    def get_rank_badge(self, obj):
        try:
            from xp_system.models import UserBadge
            # Get highest rank badge
            ub = UserBadge.objects.filter(
                user=obj.user,
                badge__rarity='rank'
            ).order_by('-badge__rank_order').first()
            
            if ub:
                return {
                    'name': ub.badge.name,
                    'image': ub.badge.image_path,
                    'rank_order': ub.badge.rank_order
                }
            return None
        except:
            return None

class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=255)
    college_name = serializers.CharField(required=True)
    year = serializers.IntegerField(required=False, allow_null=True)
    branch = serializers.CharField(max_length=255, required=False, allow_blank=True)
    roll_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    mobile_number = serializers.CharField(max_length=15, required=False, allow_blank=True)
    accepted_terms = serializers.BooleanField(required=True)
    accepted_privacy = serializers.BooleanField(required=True)
    
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_college_name(self, value):
        if not value:
            return None
        try:
            return College.objects.get(name=value)
        except College.DoesNotExist:
            raise serializers.ValidationError("Selected college is not valid.")

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    
    def validate_new_password(self, value):
        validate_password(value)
        return value

class ProfileUpdateSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.full_name', required=False)
    mobile_number = serializers.CharField(source='user.mobile_number', required=False)
    
    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio', 'theme', 'email_notifications', 'push_notifications', 'full_name', 'mobile_number']
    
    def update(self, instance, validated_data):
        user_data = {}
        if 'user' in validated_data:
            user_data = validated_data.pop('user')
        
        # Update profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update user fields
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
            
        return instance

# --- OTP Serializers ---

class SendOTPSerializer(serializers.Serializer):
    """Serialize send OTP request"""
    email = serializers.EmailField()
    type = serializers.ChoiceField(choices=['EMAIL_VERIFY', 'PASSWORD_RESET'])
    
    def validate(self, data):
        email = data['email']
        otp_type = data['type']
        
        # Check resend cooldown
        if not OTPManager.can_resend_otp(email, otp_type):
            raise serializers.ValidationError(
                "Please wait 60 seconds before requesting another OTP"
            )
        
        return data

class VerifyOTPSerializer(serializers.Serializer):
    """Serialize verify OTP request"""
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    type = serializers.ChoiceField(choices=['EMAIL_VERIFY', 'PASSWORD_RESET'])
    
    def validate_otp(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("OTP must be 6 digits")
        return value

class ResetPasswordSerializer(serializers.Serializer):
    """Serialize password reset request"""
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(
        write_only=True, 
        min_length=8,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match"}
            )
        
        # Django password validators
        try:
            validate_password(data['new_password'])
        except serializers.ValidationError as e:
            raise serializers.ValidationError(
                {"new_password": e.messages}
            )
        
        return data
    
    def validate_otp(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("OTP must be 6 digits")
        return value
