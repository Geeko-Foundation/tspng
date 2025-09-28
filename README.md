# GF:TSP:NG
##  Geeko Foundation Travel Support - The Next Generation

### Aims of this project

This is django based re-imagining of the openSUSE TSP application, aiming to fix some of the shortcomings os the original app.

We plan the following features:

- A more appealing, and easier to understand UI;
- Initial user entry of data in a self-service style;
- Use of REST APIs for bank transfers, enabling faster, more reliable payouts;
- Options for event participants to be ticketed - using QR codes and/or Google Wallet for example;
- A framework style that will enable easy addition of new features;
- Easy hosting options

### UI Framework
As a starting point I've chosen the [Daemonite Material UI 2](https://djibe.github.io/material/) design framework - only as it is what I am most familiar with.
It quickly creates usable UIs that are easy to use and understand. I have created a "dashboard" style that might be a good starting point for the UI. 
The dashboard is designed to minimize full page reload by using jquery or javascript ajax calls to retrieve rendered html or json fragments. 

### Rest API Framework
The [Ninja API Framework](https://django-ninja.dev/) is a great framework for creating REST APIs that integrate with Django.
Not strictly necessary but this point but might be useful in the future.

### Database
While Django can use most databases, there is a chance that this will be multi-tenanted - in which case Postgres is the best choice.
In which case the [django-tenant-schemas](https://django-tenant-schemas.readthedocs.io/en/latest/) package will be used. (Integration of this can be performed later)

### Banking APIs
With the advent of Open Banking, it is possible to eliminate many of the manual tasks that have plagued previous methods travel support.
Our intention is to automate as much as possible, by using APIs from banks such as [Wise](https://docs.wise.com/api-docs) or payment provider such as Stripe.

### Web and Email Notifications 
Timely notifications of events such as payments being made is essential - Web notifications can be easily used to provide this.

### 2FA/MFA
For security purposes, it is important to have 2FA/MFA in place. 

### Browser Notifications
Using browser notifications for various events is a great way to keep users informed of project progress. I've used [django-webpush](https://github.com/safwanrahman/django-webpush) 
in the past but [django-infopush](https://github.com/kilgoretrout1985/django_infopush) looks more polished, there are no doubt others. (NOTE: you can send notifications to localhost 
in test mode but to end to others you need https. I'll be setting that up on the test server soon.)

### Active Directory / LDAP Integration
Should be an option, in order to link existing LDAP accounts to the system. Single source of truth. Always!!!

### User Profile information
For obvious reasons, it is important to have a user profile containing more information than just the standard user details that Django records.
In addition some of it will be transient, such as the user's bank account details - which will recorded in Wise (or other regulated institutions) and not by us. 
This profile can be linked to AD or LDAP for example.

### Event Management
The event management system will be separate django app(s) - there are a number of django projects that have already started addressing the issue. However TSP-NG should be able to function in a standalone basis.
