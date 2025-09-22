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
As a starting point I've chosen the [Daemonite Material UI 2](https://djibe.github.io/material/) framework - only as it is what I am most familiar with.
It quickly creates usable UIs that are easy to use and understand. I have created a "dashboard" style that might be a good starting point for the UI.

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

### Active Directory / LDAP Integration
Should be an option, in order to link existing LDAP accounts to the system. Single source of truth. Always!!!
