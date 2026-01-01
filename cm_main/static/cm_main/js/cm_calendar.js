// bulma calendar integration

$(document).ready(()=>{
	// lang = navigator.language.substring(0, 2) || "en"
	lang = document.documentElement.lang || "en"
	date_fmt = get_format('SHORT_DATE_FORMAT')
	date_fmt = date_fmt.replace('d', 'dd').replace('m', 'MM').replace('y', 'yy')
	date_fmt = date_fmt.replace('Y', 'yyyy').replace('n', 'mm')

	// Initialize all input of date type.
	options = {"lang": lang, "dateFormat": date_fmt, "timeFormat": 'HH:mm:ss',
  	"todayLabel": gettext("Today"), "clearLabel": gettext("Clear"),
		"nowLabel": gettext("Now"), "cancelLabel": gettext("Cancel"),
		"validateLabel": gettext("Validate"), "displayMode": "inline",
		"enableYearSwitch" : true, "enableMonthSwitch" : true,
		"minDate": new Date(1600, 1, 1), displayMode: "dialog"
	}
	const date_calendars = [
		...bulmaCalendar.attach('[class~="dateinput"]', {'type': "date", ...options}),
		...bulmaCalendar.attach('[class~="datetimeinput"]', {'type': "datetime", ...options})
	];

	// console.log("langnav:", navigator.language, "date options:", options)
	// Loop on each date calendar initialized
	// date_calendars.forEach(calendar => {
	// 	// Add listener to select event
	// 	calendar.on('select', date => {
	// 		console.log(date);
	// 	});
	// });
});

$(document).on('htmx:afterOnLoad', () => {
	bulmaCalendar.attach('[class~="dateinput"]', {'type': "date", ...options}),
	bulmaCalendar.attach('[class~="datetimeinput"]', {'type': "datetime", ...options})
});

