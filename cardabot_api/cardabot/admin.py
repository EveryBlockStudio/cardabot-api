from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(CardaBotUser)
admin.site.register(Chat)
admin.site.register(UnsignedTransaction)
admin.site.register(FaqCategory)
admin.site.register(FaqQuestion)