# users/tokens.py
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """
    Kullanıcı hesap aktivasyonu için token oluşturucu
    """
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.is_active) + six.text_type(user.is_email_verified)
        )

account_activation_token = AccountActivationTokenGenerator()