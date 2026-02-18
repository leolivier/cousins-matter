$(document).ready(function() {
	const fullscreenContainer = $('#fullscreen-overlay');
	// Variables to store touch start and current positions for swiping
	let startX = 0;
	const minSwipeDistance = 120; // Minimum distance to detect a swipe

	// Function to open image in full screen
	function openFullscreen(imageElement) {
		// set the src of the current, next and previous images
		const currentSrc = imageElement.data('fullscreen');
		const currentPk = imageElement.data('pk');
		const swipeUrl = imageElement.data('swipe-url');

		// set photo source
		$('#image-container img').attr('src', currentSrc);
		$('#image-container').attr('hx-get', swipeUrl);
		// set photo detail url when clicked
		$('#image-container img').click(function(e) {
			e.stopPropagation();
			if (typeof get_photo_detail_url === 'function') {
				const href = get_photo_detail_url(currentPk);
				console.log("href", href);
				window.location.href = href;
			}
		})
	
		fullscreenContainer  // display the overlay
			.css('display', 'flex')
			.hide()
			.fadeIn(300);
	}

	function executeSwipe(side, diff=null) {
		console.log("executeSwipe", side);
		const container = $('#image-container');
		const url = container.attr('hx-get');
		const angle = diff ?  -diff/15 : (side === 'prev' ? -60 : 60);
		const sign = side === 'prev' ? '-' : '';
		if (url) {
			container.css({ 'transform': `translateX(${sign}150%) rotate(${angle}deg)`, 'opacity': '0' });
			htmx.ajax('GET', url, {
				target: '#swipe-container',
				values: {side: side}
			});
		}
	}
	// Touch event manager functions for swipe left/right on a card
	$(document).on('touchstart', '#image-container', function(e) {
			startX = e.originalEvent.touches[0].pageX;
			// Disable transition during swipe
			$(this).css('transition', 'none');
	});

	$(document).on('touchmove', '#image-container', function(e) {
			// Calculate displacement in real time
			const currentX = e.originalEvent.touches[0].pageX;
			let diff = currentX - startX;
			// Rotation and displacement, divide the rotation for a more natural effect
			$(this).css('transform', `translateX(${diff}px) rotate(${diff / 15}deg)`);
	});

	$(document).on('touchend', '#image-container', function(e) {
			const currentX = e.originalEvent.changedTouches[0].pageX;
			const diff = currentX - startX;
			// Reactivate transition for end animation
			// $(this).css('transition', 'transform 0.9s ease-out, opacity 0.9s ease-out');
			if (diff > minSwipeDistance) {
					// SWIPE RIGHT ==> PREV
					console.log("swipe prev", diff);
					setTimeout(() => executeSwipe("prev", diff), 20);
			} else if (diff < -minSwipeDistance) {
					// SWIPE LEFT ==> NEXT
					console.log("swipe next", diff);
					setTimeout(() => executeSwipe("next", diff), 20);
			} else {
					// CANCEL
					$(this).css('transform', 'translateX(0) rotate(0)');
			}

			startX = 0;
	});

	// Open image in full screen
	$('.gallery-image').click(function() {
		openFullscreen($(this));
	});

	// Navigate to previous image
	$('#prev-image').click(function() {
		console.log("prev-image");
		setTimeout(() => executeSwipe("prev"), 20);
	});

	// Navigate to next image
	$('#next-image').click(function() {
		console.log("next-image");
		setTimeout(() => executeSwipe("next"), 20);
	});

	// Close full screen
	$('#close-fullscreen').click(function() {
		fullscreenContainer.fadeOut(300);
	});

	// Close full screen if clicked outside image
	fullscreenContainer.find('div[class="image-container"]').click(function(e) {
		if (e.target === e.currentTarget) {
			fullscreenContainer.fadeOut(300);
		}
	});

	// Open image in full screen if URL parameter is present
	const urlParams = new URLSearchParams(window.location.search);
	if (urlParams.get('openFullscreen') === 'true') {
		openFullscreen($(`.gallery-image[data-fullscreen="${urlParams.get('firstImage')}"]`));
	}
});
