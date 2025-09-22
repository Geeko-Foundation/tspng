from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='in_group')
def in_group(user, group_name):
    group=''
    #print('user name:' +str(user))
    #print('group name:' +str(group_name))
    if Group.objects.filter(name=group_name):
        #print('group exists')
        group = Group.objects.get(name__icontains=group_name)
        #print('user is in group: '+group.name)
    return group in user.groups.all()

