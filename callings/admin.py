from django.contrib import admin
from .models import Unit, Organization, Position, Calling, CallingHistory


class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit_type', 'sort_order', 'created_at', 'updated_at')
    list_filter = ('unit_type',)
    search_fields = ('name',)
    ordering = ('sort_order', 'name')


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)


class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_leadership', 'display_order')
    list_filter = ('is_leadership',)
    search_fields = ('title',)
    ordering = ('display_order', 'title')




class CallingHistoryInline(admin.TabularInline):
    model = CallingHistory
    extra = 0
    readonly_fields = ('action', 'member_name', 'changed_by', 'changed_at', 'notes')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class CallingAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'organization', 'unit', 'status', 'date_called', 'lcr_updated')
    list_filter = ('status', 'organization', 'unit', 'lcr_updated')
    search_fields = ('name', 'position__title', 'organization__name', 'unit__name')
    date_hierarchy = 'date_called'
    inlines = [CallingHistoryInline]
    
    fieldsets = (
        ('Calling Information', {
            'fields': ('name', 'unit', 'organization', 'position', 'status')
        }),
        ('Calling Details', {
            'fields': (
                'called_by', 
                'date_called', 
                'date_sustained', 
                'date_set_apart',
                'presidency_approved',
                'hc_approved',
                'bishop_consulted_by',
            ),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('lcr_updated', 'notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


class CallingHistoryAdmin(admin.ModelAdmin):
    list_display = ('calling', 'action', 'member_name', 'changed_by', 'changed_at')
    list_filter = ('action', 'changed_at')
    search_fields = ('calling__name', 'changed_by__username', 'notes')
    date_hierarchy = 'changed_at'
    readonly_fields = ('calling', 'action', 'member_name', 'changed_by', 'changed_at', 'notes', 'snapshot')


# Register models with their admin classes
admin.site.register(Unit, UnitAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(Calling, CallingAdmin)
admin.site.register(CallingHistory, CallingHistoryAdmin)
