# from django.contrib import admin
# from .models import ExpenseCategory, Expense
#
#
# @admin.register(ExpenseCategory)
# class ExpenseCategoryAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name', 'color')
#     search_fields = ('name',)
#
#
# @admin.register(Expense)
# class ExpenseAdmin(admin.ModelAdmin):
#     list_display = ('id', 'title', 'category', 'amount', 'status', 'date')
#     list_filter = ('status', 'category', 'date')
#     search_fields = ('title', 'description')