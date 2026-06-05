from django.contrib import admin
from django.utils.html import format_html

from .models import Instructor


# ════════════════════════════════════════════════════════
#  Instructor Admin
#
#  ⚠️ instructors.CustomUser endi mavjud emas — foydalanuvchilar
#  accounts.CustomUser modeli orqali boshqariladi.
# ════════════════════════════════════════════════════════

@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display    = ('full_name', 'role_badge', 'specialty',
                       'experience_years', 'salary_fmt', 'status_badge', 'created_at')
    list_filter     = ('user__role', 'is_active')
    search_fields   = ('full_name', 'user__username', 'specialty')
    ordering        = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    actions         = ['make_active', 'make_inactive']

    # ✅ Admin paneldan qo'lda Instructor qo'shishni bloklash
    # Chunki register orqali avtomatik qo'shiladi
    def has_add_permission(self, request):
        return False

    fieldsets = (
        ('Asosiy',  {'fields': ('user', 'full_name', 'is_active')}),
        ('Profil',  {'fields': ('specialty', 'experience_years', 'salary', 'address', 'bio')}),
        ('Tizim',   {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description='Rol', ordering='user__role')
    def role_badge(self, obj):
        is_admin = obj.user.role == 'admin'
        bg  = '#7a5a10' if is_admin else '#0a4d51'
        fg  = '#f4d98f' if is_admin else '#89eff4'
        lbl = '🛡️ Admin' if is_admin else '👨‍🏫 Teacher'
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;'
            'border-radius:999px;font-size:11px;font-weight:700;">{}</span>',
            bg, fg, lbl,
        )

    @admin.display(description='Holat', ordering='is_active')
    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#8ef0bf;font-weight:700;">● Faol</span>')
        return format_html('<span style="color:#ff9aaa;font-weight:700;">● Nofaol</span>')

    @admin.display(description='Maosh', ordering='salary')
    def salary_fmt(self, obj):
        return format_html('<b>${:,.0f}</b>', obj.salary)

    @admin.action(description='✅ Faollashtirish')
    def make_active(self, request, qs):
        n = qs.update(is_active=True)
        self.message_user(request, f"{n} ta instructor faollashtirildi.")

    @admin.action(description='⛔ Nofaollashtirish')
    def make_inactive(self, request, qs):
        n = qs.update(is_active=False)
        self.message_user(request, f"{n} ta instructor nofaollashtirildi.")