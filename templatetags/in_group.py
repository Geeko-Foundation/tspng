from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='in_group')
def in_group(user, group_name):
    group = Group.objects.filter(name__icontains=group_name)
    for g in group:
        print('group found: '+str(g))
    return False # group in user.groups.all()
