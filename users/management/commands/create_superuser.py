"""
Django özel yönetim komutu: Süper kullanıcı oluştur.

Bu komut, LungVision AI uygulaması için özel süper kullanıcılar oluşturmak üzere kullanılır.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from users.models import User
import uuid


class Command(BaseCommand):
    help = 'LungVision AI için özel süper kullanıcı oluşturur'

    def add_arguments(self, parser):
        """Komut satırı argümanlarını tanımlar."""
        parser.add_argument('--email', required=True, help=_('Admin email adresi'))
        parser.add_argument('--username', required=False, help=_('Admin kullanıcı adı (opsiyonel)'))
        parser.add_argument('--password', required=True, help=_('Admin şifresi'))
        parser.add_argument('--first_name', required=False, help=_('Ad'))
        parser.add_argument('--last_name', required=False, help=_('Soyad'))
        parser.add_argument('--organization', required=False, help=_('Organizasyon adı'))
        parser.add_argument('--user_type', default='admin', 
                            choices=['admin', 'doctor', 'pathologist', 'researcher'],
                            help=_('Kullanıcı türü (admin, doctor, pathologist, researcher)'))
        
    def handle(self, *args, **options):
        """Komutu yürütür."""
        email = options['email']
        username = options['username'] or email.split('@')[0]
        password = options['password']
        first_name = options['first_name'] or ''
        last_name = options['last_name'] or ''
        organization = options['organization'] or 'LungVision Administration'
        user_type = options['user_type']
        
        # Aynı email ile kullanıcı var mı kontrol et
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'"{email}" email adresine sahip bir kullanıcı zaten var!'))
            return
        
        # Aynı kullanıcı adıyla kullanıcı var mı kontrol et
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'"{username}" kullanıcı adına sahip bir kullanıcı zaten var!'))
            return
        
        # Hesabı oluştur
        try:
            with transaction.atomic():
                admin_user = User.objects.create_user(
                    email=email,
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    organization=organization,
                    user_type=user_type,
                    is_staff=True,
                    is_superuser=True,
                    is_active=True
                )
                
            self.stdout.write(self.style.SUCCESS(
                f'"{admin_user.email}" email adresine sahip {user_type} kullanıcısı başarıyla oluşturuldu!'
            ))
            
        except Exception as e:
            raise CommandError(f'Kullanıcı oluşturulurken hata oluştu: {str(e)}')