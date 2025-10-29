"""AgentCore Identity Configuration - Cognito Authentication."""

import os
import boto3
from typing import Optional, Dict
from datetime import datetime, timedelta
import jwt


class IdentityConfig:
    """Configuration for AgentCore Identity (Cognito)."""
    
    def __init__(self):
        # Cognito Configuration
        self.USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID', '')
        self.CLIENT_ID = os.getenv('COGNITO_CLIENT_ID', '')
        self.CLIENT_SECRET = os.getenv('COGNITO_CLIENT_SECRET', '')
        self.REGION = os.getenv('AWS_REGION', 'us-east-1')
        
        # Token Configuration
        self.ACCESS_TOKEN_EXPIRY = int(os.getenv('ACCESS_TOKEN_EXPIRY', '3600'))  # 1 hour
        self.REFRESH_TOKEN_EXPIRY = int(os.getenv('REFRESH_TOKEN_EXPIRY', '2592000'))  # 30 days
        
        # Authorization Configuration
        self.ADMIN_GROUP = os.getenv('ADMIN_GROUP', 'AegisAdmins')
        self.ANALYST_GROUP = os.getenv('ANALYST_GROUP', 'AegisAnalysts')
        self.CUSTOMER_GROUP = os.getenv('CUSTOMER_GROUP', 'AegisCustomers')
        
        # Initialize Cognito client
        self._cognito_client = None
    
    @property
    def cognito_client(self):
        """Get Cognito client."""
        if not self._cognito_client:
            self._cognito_client = boto3.client('cognito-idp', region_name=self.REGION)
        return self._cognito_client
    
    def get_identity_config(self) -> dict:
        """Get identity configuration."""
        return {
            'user_pool_id': self.USER_POOL_ID,
            'client_id': self.CLIENT_ID,
            'region': self.REGION,
            'groups': {
                'admin': self.ADMIN_GROUP,
                'analyst': self.ANALYST_GROUP,
                'customer': self.CUSTOMER_GROUP
            }
        }


# Global identity config
identity_config = IdentityConfig()


class CognitoAuth:
    """Cognito authentication helper."""
    
    def __init__(self):
        self.config = identity_config
        self.client = identity_config.cognito_client
    
    def authenticate(self, username: str, password: str) -> Dict:
        """Authenticate user with Cognito."""
        try:
            response = self.client.initiate_auth(
                ClientId=self.config.CLIENT_ID,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            
            return {
                'success': True,
                'tokens': {
                    'access_token': response['AuthenticationResult']['AccessToken'],
                    'refresh_token': response['AuthenticationResult']['RefreshToken'],
                    'id_token': response['AuthenticationResult']['IdToken']
                },
                'expires_in': response['AuthenticationResult']['ExpiresIn']
            }
        except self.client.exceptions.NotAuthorizedException:
            return {
                'success': False,
                'error': 'Invalid username or password'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_token(self, access_token: str) -> Dict:
        """Verify access token."""
        try:
            response = self.client.get_user(
                AccessToken=access_token
            )
            
            # Extract user attributes
            attributes = {attr['Name']: attr['Value'] for attr in response['UserAttributes']}
            
            return {
                'valid': True,
                'username': response['Username'],
                'attributes': attributes
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def get_user_groups(self, username: str) -> list:
        """Get user's group memberships."""
        try:
            response = self.client.admin_list_groups_for_user(
                Username=username,
                UserPoolId=self.config.USER_POOL_ID
            )
            
            return [group['GroupName'] for group in response['Groups']]
        except Exception as e:
            print(f"Failed to get user groups: {e}")
            return []
    
    def has_permission(self, username: str, required_group: str) -> bool:
        """Check if user has required permission."""
        user_groups = self.get_user_groups(username)
        return required_group in user_groups
    
    def refresh_token(self, refresh_token: str) -> Dict:
        """Refresh access token."""
        try:
            response = self.client.initiate_auth(
                ClientId=self.config.CLIENT_ID,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters={
                    'REFRESH_TOKEN': refresh_token
                }
            )
            
            return {
                'success': True,
                'tokens': {
                    'access_token': response['AuthenticationResult']['AccessToken'],
                    'id_token': response['AuthenticationResult']['IdToken']
                },
                'expires_in': response['AuthenticationResult']['ExpiresIn']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_user(
        self,
        username: str,
        email: str,
        temporary_password: str,
        groups: Optional[list] = None
    ) -> Dict:
        """Create a new user."""
        try:
            # Create user
            response = self.client.admin_create_user(
                UserPoolId=self.config.USER_POOL_ID,
                Username=username,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'email_verified', 'Value': 'true'}
                ],
                TemporaryPassword=temporary_password,
                MessageAction='SUPPRESS'  # Don't send welcome email
            )
            
            # Add user to groups
            if groups:
                for group in groups:
                    self.client.admin_add_user_to_group(
                        UserPoolId=self.config.USER_POOL_ID,
                        Username=username,
                        GroupName=group
                    )
            
            return {
                'success': True,
                'username': username,
                'user_status': response['User']['UserStatus']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_user(self, username: str) -> Dict:
        """Delete a user."""
        try:
            self.client.admin_delete_user(
                UserPoolId=self.config.USER_POOL_ID,
                Username=username
            )
            
            return {
                'success': True,
                'message': f'User {username} deleted'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# Global auth instance
cognito_auth = CognitoAuth()

