// Most of this code is borrowed from the galleries app readapted for small galleries
let currentImage = null;
let fullscreenContainer = null;
// Variables to store touch start and end positions for swiping
let touchStartX = 0;
let touchEndX = 0;
const minSwipeDistance = 50; // Minimum distance to detect a swipe
const screenWidth = window.innerWidth;

function initPrevNext() {
	const photoItems = $('.photo-item');
	photoItems.each(function(index) {
		const item = $(this);
		// Define data-prev
		if (index > 0) {
				const prevFullscreenUrl = photoItems.eq(index - 1).data('fullscreen');
				if (prevFullscreenUrl) {
						item.data('prev', prevFullscreenUrl);
				}
		} else {  // no previous image, use the last one to rotate
				const lastFullscreenUrl = photoItems.eq(photoItems.length - 1).data('fullscreen');
				if (lastFullscreenUrl) {
						item.data('prev', lastFullscreenUrl);
				}
		}
		// Define data-next
		if (index < photoItems.length - 1) {
				const nextFullscreenUrl = photoItems.eq(index + 1).data('fullscreen');
				if (nextFullscreenUrl) {
						item.data('next', nextFullscreenUrl);
				}
		} else {  // no next image, use the 1rst one to rotate
				const firstFullscreenUrl = photoItems.eq(0).data('fullscreen');
				if (firstFullscreenUrl) {
						item.data('next', firstFullscreenUrl);
				}
		}
	});
}
// Function to open image in full screen 
function openFullscreen(imageElement) {
	currentImage = imageElement;
	// set the src of the current, next and previous images
	let currentSrc = imageElement.data('fullscreen');
	let nextSrc = imageElement.data('next');
	let prevSrc = imageElement.data('prev');
	
	// Update the src of the current, next and previous images
	$('.image-wrapper.prev img').attr('src', prevSrc);
	$('.image-wrapper.current img').attr('src', currentSrc);
	$('.image-wrapper.next img').attr('src', nextSrc);
	fullscreenContainer  // display the overlay
		.css('display', 'flex')
		.hide()
		.fadeIn(300);
}

function createNewWrapper(direction, translation, image_url) {
	const newWrapper = $(`<div class="image-wrapper ${direction}">`)
		.css('transform', translation)
		.append(`<div class="image-container"><img src="${image_url}"></div>`);
	newWrapper.find('.image-container').click(function(e) {
		if (e.target === e.currentTarget) {
			fullscreenContainer.fadeOut(300);
		}
	});
	fullscreenContainer.append(newWrapper);
}

// Swipe left -> next image
function navigateToNext() {
	newSrc = $('.image-wrapper.next img').attr('src');
	if (!newSrc) { // should never happen
		alert('next image not found');
		return
	}
	newItem = $('.photo-item').filter(function(index) {
		return $(this).data('fullscreen') === newSrc;
	}).first()

	// swipe left
	$('.image-wrapper.current').css('transform', 'translateX(-100%)');
	$('.image-wrapper.next').css('transform', 'translateX(0)');
	// the prev is removed and replaced by the current
	$('.image-wrapper.prev').remove();
	$('.image-wrapper.current').removeClass('current').addClass('prev');
	// the next becomes the current
	$('.image-wrapper.next').removeClass('next').addClass('current');
	// the next must be created: preload the new next image and create the new next wrapper
	newNextSrc = newItem.data('next');
	if (!newNextSrc) { // should never happen
		alert('next image not found');
		return
	}
	createNewWrapper('next', 'translateX(100%)', newNextSrc)
}

// Swipe right -> previous image
function navigateToPrevious() {
	newSrc = $('.image-wrapper.prev img').attr('src');
	if (!newSrc) { // should never happen
		alert('previous image not found');
		return
	}
	newItem = $('.photo-item').filter(function(index) {
		return $(this).data('fullscreen') === newSrc;
	}).first()

	// swipe right
	$('.image-wrapper.current').css('transform', 'translateX(100%)');
	$('.image-wrapper.prev').css('transform', 'translateX(0)');
	// the next is removed and replaced by the current
	$('.image-wrapper.next').remove();
	$('.image-wrapper.current').removeClass('current').addClass('next');
	// the prev becomes the current
	$('.image-wrapper.prev').removeClass('prev').addClass('current');
	// the prev must be created: preload the new prev image and create the new prev wrapper
	newPrevSrc = newItem.data('prev');
	if (!newPrevSrc) { // should never happen
		alert('previous image not found');
		return
	}
	createNewWrapper('prev', 'translateX(-100%)', newPrevSrc)
}

$(document).ready(function() {
	initPrevNext();
	fullscreenContainer = $('#fullscreen-overlay'); // initialize Full-screen image container

	// Touch event manager functions
	fullscreenContainer.on('touchstart', function(e) {
		touchStartX = e.originalEvent.touches[0].clientX;
		// Disable transition during swipe
		$('.image-wrapper').css('transition', 'none');
	});

	fullscreenContainer.on('touchmove', function(e) {
		// Prevent page scrolling by default
		e.preventDefault();
		// Calculate displacement in real time
		const currentX = e.originalEvent.touches[0].clientX;
		const deltaX = currentX - touchStartX;
		// Move current image
		$('.image-wrapper.current').css('transform', `translateX(${deltaX}px)`);
		// Move next or previous image
		if (deltaX < 0) {
				// Swipe left, prepare next image
				$('.image-wrapper.next')
						.css('transform', `translateX(calc(100% + ${deltaX}px))`);
		} else {
				// Swipe right, prepare previous image
				$('.image-wrapper.prev')
						.css('transform', `translateX(calc(-100% + ${deltaX}px))`);
		}
	});

	fullscreenContainer.on('touchend', function(e) {
		touchEndX = e.originalEvent.changedTouches[0].clientX;
		const deltaX = touchEndX - touchStartX;
		// Reactivate transition for end animation
		$('.image-wrapper').css('transition', 'transform 0.3s ease-out');			
		if (Math.abs(deltaX) > minSwipeDistance) {
			if (deltaX > 0) {
				navigateToPrevious();
			} else {
				navigateToNext();
			}
		} else {
			// Return to initial position if swipe not long enough
			$('.image-wrapper.current').css('transform', 'translateX(0)');
			$('.image-wrapper.next').css('transform', 'translateX(100%)');
			$('.image-wrapper.prev').css('transform', 'translateX(-100%)');
		}
	});

	// Open image in full screen
	$('.photo-item').click(function() {
		openFullscreen($(this));
	});

	// Navigate to previous image
	$('#prev-image').click(function() {
		navigateToPrevious();
	});

	// Navigate to next image
	$('#next-image').click(function() {
		navigateToNext();
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
