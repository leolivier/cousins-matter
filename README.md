<div style="display:block; align-items:center">

![GitHub Release](https://img.shields.io/github/v/release/leolivier/cousins-matter) ![GitHub Release Date](https://img.shields.io/github/release-date/leolivier/cousins-matter) [![GitHub CI release build status badge](https://github.com/leolivier/cousins-matter/actions/workflows/publish-image-on-release.yml/badge.svg)](https://github.com/leolivier/cousins-matter/actions?query=workflow%Release+build) ![GitHub commits since latest release](https://img.shields.io/github/commits-since/leolivier/cousins-matter/latest)

 ![GitHub License](https://img.shields.io/github/license/leolivier/cousins-matter) ![GitHub top language](https://img.shields.io/github/languages/top/leolivier/cousins-matter) [![Django](https://img.shields.io/badge/Django-5.0.2-green)](https://www.djangoproject.com/) 

![GitHub Issues or Pull Requests](https://img.shields.io/github/issues-closed-raw/leolivier/cousins-matter) ![GitHub Issues or Pull Requests](https://img.shields.io/github/issues-raw/leolivier/cousins-matter) [![GitHub CI push build status badge](https://github.com/leolivier/cousins-matter/actions/workflows/publish-image-on-push.yml/badge.svg?branch=main)](https://github.com/leolivier/cousins-matter/actions?query=workflow%3APush+build) 

</div>

<table>
 <tr>
  <td width="50%"><img src='https://raw.githubusercontent.com/leolivier/cousins-matter/main/cm_main/static/cm_main/images/cousinades.png' title="Cousins Matter!"></td>
  <td> <h1>Cousins Matter project</h1>
   <p>An application for managing large families, listing all your cousins and allowing them to manage their own profiles. It also provide various features like photo galleries, forums, chat rooms, ...</p>
  </td>
 </tr>
</table>

# Table of Content
* [Features](#features)
  * [Translations](#translations)
  * [Member Management](#member-management)
  * [Galleries](#galleries)
  * [Forum](#forum)
  * [Chat](#chat)
  * [Documentation](#documentation)
  * [Coming soon](#coming-soon)

# Features

## Translations
* Comes with English and French translations
* Can be easily translated into any LTR language, see [documentation](https://github.com/leolivier/cousins-matter/wiki#translate-to-a-new-language). Not tested for RTL.

## Member Management
* Site admin can invite their cousins by email
* Anyone can request an invitation which will be emailed to the site admin who can then invite them. Invitation requests are protected by a captcha.
* Members can create "managed" members, i.e. members who are not active on the site (e.g. for small children or elderly people)
* Managed members can be activated by their managing members (e.g. when a child is old enough to be active on the site).
* Members can be imported in bulk via CSV files
* Member list can be filtered by first and last name
* Members can update their own profile and the profile of the members they manage
* A directory of members can be printed in PDF format
* Birthdays in the next 50 days can be displayed (50 can be changed in settings)

## Galleries
* All active members can create galleries and add photos to them
* Galleries can have sub galleries of any depth
* Photos can be imported in bulk using zip files. Each folder in the zip file becomes a gallery. Updates are managed
* Gallery photo display is paginated

## Forum
* Active members can create posts
* Active members can reply to other members' posts or add simple comments

## Chat
* Connected members can chat in live mode with other connected members
* Cousins Matter manages as many chat rooms as requested

# Pages / CMS
Basic CMS features: admins can create static HTML pages and publish them on the site. 
The home page can also be configured this way. 

## Documentation
* The documentation for installing, upgrading and running the application in on the wiki [Home](https://github.com/leolivier/cousins-matter/wiki) page.
* The settings are documented on the wiki [Settings](https://github.com/leolivier/cousins-matter/wiki/settings) page.

## Coming soon
  * Help/faq/about
  * Classifieds from all members
  * Event Planner (Cousinades)
  * Genealogy
  * Polls
  * Color Themes
  * ...
