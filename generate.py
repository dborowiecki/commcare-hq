#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
from generateCouchData import generate_user
from generateCouchData import generate_domain
from generateCouchData import generate_forms
user_name = 'webu2@dboro.commcarehq.org'
first_name = 'u6f'
sec_name = 'u6s'
email = 'u6'
user_domain = 'asdf'
uuid = '1eb9c0b1ceac4967a947fb267f7004fe'
print('Start generation')


ug = generate_user.UserGenerator()
dg = generate_domain.DomainGenerator()
ag = generate_forms.AppGenerator()
deploy = generate_domain.DeploymentGenerator()
# #u = generate_user.UserGenerator().create_user(user_domain, user_name, first_name=first_name,last_name=sec_name,
# #                                              email=email, user_type='WebUser')
u = ug.get_user_by_name('generated2@dboro.commcarehq.org')

# ug.add_to_domain(u, 'dboro')
# ug.get_user_by_name(user_name)

new_domain = dg.create_domain('4thdomain')

#fg = generate_forms.FormGenerator(new_domain)
fg2 = generate_forms.FormGenerator2().foo()
#print("Adding form {}".format(fg.add_form('simple_form.xml')))

# random_deploy = deploy.create_deployment('Bytom', ['PL'],
#                                          'EU', 'My second deployment')
#
# dg.add_deployment(new_domain, random_deploy)
# dg.add_organization(new_domain, 'organizacja')
# u = ug.get_user_by_name('asdf@asdf.asdf')
# dg.change_edition(new_domain, 'enterprise')
# dg.set_areas(new_domain, 'Health', 'Maternal, Newborn, & Child Health')
# print('Area: {}'.format(new_domain.name))
# print('Deploy: {}'.format(new_domain.deployment))
# print('Organization: {}'.format(new_domain.organization_name))
# dg.change_project_state(new_domain, "transition")
# dg.change_business_unit(new_domain, 'INC')

# new_app = ag.generate_app('4thdomain', 'Cool App')
# apps = ag.get_domain_apps(new_domain)
# new_app = apps[0]
# for app in apps:
#     if app.name == 'Cool App':
#         print("Deleting app")
#         print(app.delete_app())
#
# new_domain.save()
# apps2 = ag.get_domain_apps(new_domain)
# mode = ag.generate_module(new_app, 'Cooler1 module')
# form = ag.generate_form(new_app, mode, 'Super Form')
# form = ag.generate_form(new_app, mode, 'Super Form')
#rec_mode = new_app.modules
# print('Domain apps: {}'.format([x.name for x in apps]))
# print('Domain apps2: {}'.format([x.name for x in apps2]))
#print("Modules: {}".format([x.name for x in rec_mode]))
#print("Forms: {}".format(([x.name for x in new_app.get_forms()])))


