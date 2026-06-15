from django.contrib import admin

from .models import AILog


@admin.register(AILog)
class AILogAdmin(admin.ModelAdmin):
    list_display  = ('feature', 'related_object', 'success', 'model_name',
                     'input_tokens', 'output_tokens', 'created_by', 'created_at')
    list_filter   = ('feature', 'success', 'created_at')
    search_fields = ('related_object', 'prompt', 'response', 'error')
    readonly_fields = [f.name for f in AILog._meta.fields]

    def has_add_permission(self, request):
        return False
