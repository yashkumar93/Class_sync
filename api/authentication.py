from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from supabase import create_client, Client
from core.models import User

class SupabaseJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        
        try:
            supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            # This calls the Supabase API to validate the token and fetch the user
            # It's more secure than local decoding if we don't have the JWT Secret
            user_res = supabase.auth.get_user(token)
            supabase_user = user_res.user
        except Exception as e:
            raise AuthenticationFailed('Invalid or expired Supabase token')

        if not supabase_user:
            raise AuthenticationFailed('User not found in Supabase')

        # Find or create the Django user based on Supabase UUID or Email
        # In a real migration, we'd want to match by email first if they existed before Supabase
        user = User.objects.filter(supabase_uid=supabase_user.id).first()
        
        if not user and supabase_user.email:
            user = User.objects.filter(email=supabase_user.email).first()
            if user:
                # Link existing user
                user.supabase_uid = supabase_user.id
                user.save(update_fields=['supabase_uid'])
                
        if not user:
            # Create a new user (defaulting to student role, can be changed by admin)
            email_val = supabase_user.email or ""
            username_val = supabase_user.email or str(supabase_user.id)
            user = User.objects.create_user(
                username=username_val,
                email=email_val,
                role=User.ROLE_STUDENT,
                supabase_uid=supabase_user.id
            )
            
        return (user, token)
