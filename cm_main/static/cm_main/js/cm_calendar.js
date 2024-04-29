// bulma calendar integration

document.addEventListener('DOMContentLoaded', () => {
	lang = navigator.language.substring(0, 2) || "en"
	fmt = get_format('SHORT_DATE_FORMAT')
	fmt = fmt.replace('d', 'dd').replace('m', 'MM').replace('y', 'yy')
	fmt = fmt.replace('Y', 'yyyy').replace('n', 'mm')

	// Initialize all input of date type.
	options = {'type': "date", "lang": lang, "dateFormat": fmt, 
  	"todayLabel": gettext("Today"), "clearLabel": gettext("Clear"),
		"nowLabel": gettext("Now"), "cancelLabel": gettext("Cancel"),
		"validateLabel": gettext("Validate"), "displayMode": "inline",
		"enableYearSwitch" : true, "enableMonthSwitch" : true,
		"minDate": new Date(1600, 1, 1)
	}
	const calendars = bulmaCalendar.attach('[class~="dateinput"]', options);

	console.log("langnav:", navigator.language, "options:", options)
	// Loop on each calendar initialized
	calendars.forEach(calendar => {
		// Add listener to select event
		calendar.on('select', date => {
			console.log(date);
		});
	});
});

