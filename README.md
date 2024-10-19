
![Cousins Matter!](https://raw.githubusercontent.com/leolivier/cousins-matter/main/cm_main/static/cm_main/images/cousinades.jpg)


# Cousins Matter project

An application for managing large families, listing all your cousins and allowing them to manage their own profiles. It also provide various features like photo galleries, forums, chat rooms, ...

## Badges

![GitHub Release](https://img.shields.io/github/v/release/leolivier/cousins-matter) ![GitHub Release Date](https://img.shields.io/github/release-date/leolivier/cousins-matter) [![GitHub CI release build status badge](https://github.com/leolivier/cousins-matter/actions/workflows/publish-image-on-release.yml/badge.svg)](https://github.com/leolivier/cousins-matter/actions?query=workflow%Release+build) ![GitHub commits since latest release](https://img.shields.io/github/commits-since/leolivier/cousins-matter/latest)

 ![GitHub License](https://img.shields.io/github/license/leolivier/cousins-matter) ![GitHub top language](https://img.shields.io/github/languages/top/leolivier/cousins-matter) [![Django](https://img.shields.io/badge/Django-5.0.2-green)](https://www.djangoproject.com/) 

![GitHub Issues or Pull Requests](https://img.shields.io/github/issues-closed-raw/leolivier/cousins-matter) ![GitHub Issues or Pull Requests](https://img.shields.io/github/issues-raw/leolivier/cousins-matter) [![GitHub CI push build status badge](https://github.com/leolivier/cousins-matter/actions/workflows/publish-image-on-push.yml/badge.svg?branch=main)](https://github.com/leolivier/cousins-matter/actions?query=workflow%3APush+build) 
## Features

### Member Management
* Site admin can invite their cousins by email
* Anyone can request an invitation which will be emailed to the site admin who can then invite them. Invitation requests are protected by a captcha.
* Members can create "managed" members, i.e. members who are not active on the site (e.g. for small children or elderly people)
* Managed members can be activated by their managing members (e.g. when a child is old enough to be active on the site).
* Members can be imported in bulk via CSV files
* Member list can be filtered by first and last name
* Members can update their own profile and the profile of the members they manage
* A directory of members can be printed in PDF format
* Birthdays in the next 50 days can be displayed (50 can be changed in settings)

### Galleries
* All active members can create galleries and add photos to them
* Galleries can have sub galleries of any depth
* Photos can be imported in bulk using zip files. Each folder in the zip file becomes a gallery. Updates are managed
* Gallery photo display is paginated

### Forum
* Active members can create posts
* Active members can reply to other members' posts or add simple comments

### Chat
* Connected members can chat in live mode with other connected members
* Cousins Matter manages as many chat rooms as requested
* Members can create private chat rooms and select the members who can participate in these rooms. 
  The creator of the room becomes admin in this room and can add other members and elect admins in these members.
  Admins can invite other members and other admins

## Pages / CMS
Basic CMS features: admins can create static HTML pages and publish them on the site. 
The home page can also be configured this way as well as the privcay policy, the about pages... 

## Theming
Admin can easily define their own theme (colors, font, ...). See [Themes](https://github.com/leolivier/cousins-matter/wiki/customization#themes)

## Translations
* Comes with manual English and French translations
* **NEW**: Translated into Spanish, German, Portuguese and Italian using [auto-po-lyglot](https://github.com/leolivier/auto-po-lyglot/) automated translations based on AI LLMs (various LLMs were used depending on the language).
  **WARNING**: Because these translations are automated, they may sometimes be incorrect or inaccurate. Please open issues on Github if you find errors.
* Can be easily translated into any LTR language, see [documentation](https://github.com/leolivier/cousins-matter/wiki#translate-to-a-new-language). Not tested for RTL.

## Documentation

* The documentation for installing, upgrading and running the application in on the wiki [Home](https://github.com/leolivier/cousins-matter/wiki) page.
* The settings are documented on the wiki [Settings](https://github.com/leolivier/cousins-matter/wiki/settings) page.
* The customization (apart from the settings) is described at [Customization](https://github.com/leolivier/cousins-matter/wiki/customization)

## Authors

- [@leolivier](https://www.github.com/leolivier)

