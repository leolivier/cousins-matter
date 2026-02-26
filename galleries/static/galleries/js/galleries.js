$(document).ready(function() {
	const fullscreenContainer = $('#fullscreen-overlay');
	// Variables to store touch start and current positions for swiping
	let startX = 0;
	const minSwipeDistance = 120; // Minimum distance to detect a swipe

	// Function to open image or video in full screen
	function openFullscreen(imageElement) {
		const swipeUrl = imageElement.data('swipe-url');
		const pk = imageElement.data('pk');
		const isVideo = imageElement.data('is-video');

		// Trigger HTMX to load the initial image or video content
		htmx.ajax('GET', swipeUrl+ "#image", {
			target: '#swipe-container'
		});

		fullscreenContainer  // display the overlay
			.css('display', 'flex')
			.hide()
			.fadeIn(300);
	}


	function executeSwipe(side, diff=null) {
		console.log("executeSwipe", side);
		const container = $('#image-container');
		const pk = container.data('pk');
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
			if (diff > minSwipeDistance) {
					// SWIPE RIGHT ==> PREV
					// console.log("swipe prev", diff);
					setTimeout(() => executeSwipe("prev", diff), 20);
			} else if (diff < -minSwipeDistance) {
					// SWIPE LEFT ==> NEXT
					// console.log("swipe next", diff);
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
		fullscreenContainer.find('#image-container').html('');
	});

	// Close full screen if clicked outside image
	fullscreenContainer.find('div[class="image-container"]').click(function(e) {
		if (e.target === e.currentTarget) {
			fullscreenContainer.fadeOut(300);
			fullscreenContainer.find('#image-container').html('');
		}
	});

	// Open image in full screen if URL parameter is present
	const urlParams = new URLSearchParams(window.location.search);
	if (urlParams.get('openFullscreen') === 'true') {
		openFullscreen($(`.gallery-image[data-fullscreen="${urlParams.get('firstImage')}"]`));
	}

	// Slideshow logic
	let slideshowTimer = null;
	const slideshowDelay = (parseInt($('#slideshow-toggle').data('delay')) || 5) * 1000;

	function startSlideshowTimer() {
		stopSlideshowTimer(); // Clear any existing timer
		slideshowTimer = setTimeout(function() {
			executeSwipe("next");
		}, slideshowDelay);
	}

	function stopSlideshowTimer() {
		if (slideshowTimer) {
			clearTimeout(slideshowTimer);
			slideshowTimer = null;
		}
	}

	function toggleSlideshow() {
		const btn = $('#slideshow-toggle');
		const icon = $('#slideshow-icon');
		const fullscreenBtn = $('#fullscreen-slideshow-toggle');
		const fullscreenIcon = $('#fullscreen-slideshow-icon');
		const isActive = btn.hasClass('is-active');

		if (isActive) {
			// Stop slideshow
			btn.removeClass('is-active');
			icon.removeClass('mdi-pause').addClass('mdi-play');
			fullscreenBtn.removeClass('is-active');
			fullscreenIcon.removeClass('mdi-pause').addClass('mdi-play');
			stopSlideshowTimer();
		} else {
			// Start slideshow
			btn.addClass('is-active');
			icon.removeClass('mdi-play').addClass('mdi-pause');
			fullscreenBtn.addClass('is-active');
			fullscreenIcon.removeClass('mdi-play').addClass('mdi-pause');

			// If not already in fullscreen, open the first image
			if (fullscreenContainer.css('display') === 'none') {
				const firstImage = $('.gallery-image').first();
				if (firstImage.length > 0) {
					openFullscreen(firstImage);
				}
			}
			startSlideshowTimer();
		}
	}

	$('#slideshow-toggle, #fullscreen-slideshow-toggle').click(function(e) {
		e.stopPropagation(); // Prevent closing fullscreen
		toggleSlideshow();
	});

	// Initial state for fullscreen slideshow button when opening fullscreen
	function syncFullscreenButton() {
		const isActive = $('#slideshow-toggle').hasClass('is-active');
		const fullscreenIcon = $('#fullscreen-slideshow-icon');
		const fullscreenBtn = $('#fullscreen-slideshow-toggle');

		if (isActive) {
			fullscreenBtn.addClass('is-active');
			fullscreenIcon.removeClass('mdi-play').addClass('mdi-pause');
		} else {
			fullscreenBtn.removeClass('is-active');
			fullscreenIcon.removeClass('mdi-pause').addClass('mdi-play');
		}
	}

	$(document).on('click', '.gallery-image', function() {
		syncFullscreenButton();
	});

	// Automatically move to the next slide when content is loaded, if slideshow is active
	$(document).on('htmx:afterOnLoad', function(evt) {
		if (evt.detail.target.id === 'swipe-container' && $('#slideshow-toggle').hasClass('is-active')) {
			startSlideshowTimer();
		}
	});

	// Reset timer on manual navigation
	$('#prev-image, #next-image').click(function() {
		if ($('#slideshow-toggle').hasClass('is-active')) {
			startSlideshowTimer();
		}
	});

	// Stop slideshow when fullscreen is closed
	$('#close-fullscreen').click(function() {
		if ($('#slideshow-toggle').hasClass('is-active')) {
			toggleSlideshow();
		}
	});
});
