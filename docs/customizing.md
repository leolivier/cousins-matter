# Customize your site

## Settings
See [Settings](settings.md) for customization by changing the settings.

### Features management
Using the settings, you can also manage the features that will be offered to members as explained in [Features management](settings.md/#features-management)

## Creating pages
Admin can create or update static pages using the "Edit Page" feature in the navigation bar. **Only Admins have access to this feature!**

When creating a page, a form opens and you have to fill some fields:

* URL: This field will be used to display the page.
	There are different page categories:

	* "About" pages including the privacy policy described below, must start with '/<language-code\>/about/<page-slug\>'. They are displayed on the right side of the nav bar under a question mark icon.
	* "Home" pages are pages that start with '/<language-code\>/home/'. See [Front or Home Page](#front-or-home-pages) below
	* "Static" pages are pages that start with '/publish/'. They can have 2 subforms: 

		* /publish/<page-slug\>: the title of these pages is displayed directly in the Pages menu of the navbar.
		* /publish/<menu-name\>/<page-slug\>: These are drop-down menus of the Pages menu with the name "menu-name", and the title of each page is displayed in the drop-down list under <menu-name\>.

	* Message pages, with a URL starting with '/admin-message/', see [Showing an admin message on all pages](#show-an-admin-message-on-all-pages)
	* Any other URL can be included as a link in other pages but won't be accessible from the menu bar.

* Title: this is the string that will be displayed in the menus.
* Content: this is the content of the page. It can be edited using the rich editor.
* A checkbox called "Authorize comments" is shown but not used at the moment.

## Privacy Management
Static pages (one per language) describing the site's privacy policy are loaded into the database during application installation.
These pages can be customized using the standard "Edit Page" feature described above.

**WARNING**: Don't change the URL of these pages! The pattern for this URL is /<language-code\>/about/privacy-policy. If you change this pattern, the associated privacy policy won't be accessible anymore!

## Custom footer
Set `SITE_FOOTER` as explained in [General customization](settings.md/#general-customization)

## Front (or Home) pages
Your site needs two different front (aka home) pages: 

* The first one for unauthenticated people, where you can explain the purpose of your site without giving too many details and nothing private.
* The second is the page for your members once they are logged in.
You can edit these 2 pages directly from the default homepage or from the list of pages in the menu.

The URL of these pages is built like this: /<language code\>/home/authenticated and /<language code\>/home/unauthenticated.

Predefined versions of these two pages are loaded in the database at first load. 
If the language code in the .env doesn't correspond to any of the preloaded pages, the en-US version is displayed.

**CAUTION**: Do not change the URLs of these pages or it won't work!!!

## Show an admin message on all pages
Administrators can create special pages with a URL starting with '/admin-message/'. The title of this page will only be used in the page list of the "Edit pages" menu. The content of these pages is displayed as a notification at the top of each page and can be closed but will reappear on each new connection as long as the page exists in the database.

You can create either one page with URL '/admin-message/' or any number of pages all starting with '/admin-message/' and each page will be displayed as a specific notification.

## Themes
To create your own theme, you need to apply new values to Bulma variables in the file named media/public/theme.css (this file is mounted in the docker images).

The customization must have the following format:

```css
:root {
	--bulma-xxx: value;
	--bulma-yyy: value;
	--bulma-zzz: value;
}
```

e.g.

```css
:root {
	--bulma-body-font-size: 16px;
	--bulma-primary-h: 155deg !important;
	--bulma-primary-s: 80% !important;
	--bulma-primary-l: 37% !important;
}
```

will change the global font size of the site and change the primary color (defined in terms of HSL (Hue, Saturation, and Lightness). 
(You can try the HSL colors at https://hslpicker.com/)

You can also change these variables in the component scope but then it's not a real theme anymore, see details on [Bulma CSS Variables](https://bulma.io/documentation/features/css-variables/) and [Customizing Bulma with CSS variables](https://bulma.io/documentation/customize/with-css-variables/)

To know all available CSS Variables defined by Bulma, please have a look at the [Bulma CSS File](https://cdn.jsdelivr.net/npm/bulma@1.0.1/css/bulma.css) and test them in your browser to see the effect.

