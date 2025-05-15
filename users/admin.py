# users/admin.py
from django.contrib import admin
from .models import User  # Varsayılan Django User modelini içe aktarıyoruz

# Standart User modeli için admin kaydı
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Kişisel Bilgiler', {'fields': ('first_name', 'last_name', 'profile_image')}),
        ('Mesleki Bilgiler', {'fields': ('user_type', 'organization', 'specialty', 'phone_number')}),
        ('İzinler', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Önemli tarihler', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'user_type', 'is_staff', 'is_active'),
        }),
    )

# MongoUserAdmin kodunu şimdilik yorum satırına alın
"""
class MongoUserAdmin(admin.ModelAdmin):
    # ... (önceki kod)

# Admin sitesine kaydı yorum satırına alın
# admin.site.register(MongoUser, MongoUserAdmin)
"""