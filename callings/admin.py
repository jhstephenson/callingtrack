from django.contrib import admin
from .models import Unit, Organization, Position, Member, Calling, CallingHistory


class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit_type', 'created_at', 'updated_at')
    list_filter = ('unit_type',)
    search_fields = ('name',)


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)


class PositionInline(admin.TabularInline):
    model = Position
    extra = 1


class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'is_leadership', 'display_order')
    list_filter = ('organization', 'is_leadership')
    search_fields = ('title',)
    ordering = ('organization', 'display_order', 'title')


class MemberAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'home_unit', 'email', 'phone')
    list_filter = ('home_unit', 'membership_status')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Personal Information', {
            'fields': (
                ('first_name', 'middle_name', 'last_name', 'suffix'),
                'gender',
                'birth_date',
                'profile_picture',
            )
        }),
        ('Contact Information', {
            'fields': (
                'email',
                'phone',
                'address',
                'city',
                'state',
                'zip_code',
            )
        }),
        ('Membership Information', {
            'fields': (
                'membership_status',
                'home_unit',
                'is_active',
            )
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Name'
    get_full_name.admin_order_field = 'last_name'
    ordering = ('last_name', 'first_name')


class CallingHistoryInline(admin.TabularInline):
    model = CallingHistory
    extra = 0
    readonly_fields = ('action', 'member', 'changed_by', 'changed_at', 'notes')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class CallingAdmin(admin.ModelAdmin):
    list_display = ('member', 'position', 'unit', 'status', 'date_called', 'lcr_updated')
    list_filter = ('status', 'position__organization', 'unit', 'lcr_updated')
    search_fields = ('member__name', 'position__title', 'unit__name')
    date_hierarchy = 'date_called'
    inlines = [CallingHistoryInline]
    
    fieldsets = (
        ('Calling Information', {
            'fields': ('member', 'position', 'unit', 'status')
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
    list_display = ('calling', 'action', 'member', 'changed_by', 'changed_at')
    list_filter = ('action', 'changed_at')
    search_fields = ('calling__member__name', 'changed_by__name', 'notes')
    date_hierarchy = 'changed_at'
    readonly_fields = ('calling', 'action', 'member', 'changed_by', 'changed_at', 'notes', 'snapshot')


# Register models with their admin classes
admin.site.register(Unit, UnitAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Calling, CallingAdmin)
admin.site.register(CallingHistory, CallingHistoryAdmin)
