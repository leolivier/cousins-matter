// WARNING! the following variables must be filled before including this file
// $photos_count, $image_url, $photo_url

let currentImage = null;
let fullscreenContainer = null;
// Variables to store touch start and end positions for swiping
let touchStartX = 0;
let touchEndX = 0;
const minSwipeDistance = 50; // Minimum distance to detect a swipe
const screenWidth = window.innerWidth;

// Function to open image in full screen
function openFullscreen(imageElement) {
	currentImage = imageElement;
	// set the src of the current, next and previous images
	let currentSrc = imageElement.data('fullscreen');
	let nextSrc = imageElement.data('next');
	let prevSrc = imageElement.data('prev');
	let currentIdx = imageElement.data('idx');
	let currentPk = imageElement.data('pk');

	$('.image-wrapper.prev img').attr('src', prevSrc);
	$('.image-wrapper.current img').attr('src', currentSrc);
	$('.image-wrapper.next img').attr('src', nextSrc);
	// set photo url
	$('.image-wrapper.current img').click(function(e) {
		window.location.href = getPhotoUrl(currentPk);
	})
	// initialize current image pks
	$.ajax({
		url: getImageUrl(currentIdx - 1),
		method: 'GET',
		success: function(response) {
			$('.image-wrapper.prev').click(function(e) {
					window.location.href = getPhotoUrl(response.pk);
				})
			}
		});
	$.ajax({
		url: getImageUrl(currentIdx + 1),
		method: 'GET',
		success: function(response) {
			$('.image-wrapper.next').click(function(e) {
				window.location.href = getPhotoUrl(response.pk);
			})
			}
		});
	
	// Update the current image IDX
	fullscreenContainer.data('current-image-idx', currentIdx)
	fullscreenContainer  // display the overlay
		.css('display', 'flex')
		.hide()
		.fadeIn(300);
}

function getImageUrl(photo_pk) {
	return $image_url.replace('1234567890', photo_pk);
}

function getPhotoUrl(photo_pk) {
	return $photo_url.replace('1234567890', photo_pk);
}

function createNewWrapper(direction, translation, image_url, photo_pk) {
	const newWrapper = $(`<div class="image-wrapper ${direction}">`)
		.css('transform', translation)
		.append(`<div class="image-container"><img src="${image_url}"></div>`);
	newWrapper.find('.image-container').click(function(e) {
		if (e.target === e.currentTarget) {
			fullscreenContainer.fadeOut(300);
		}
	});
	newWrapper.find('img').click(function(e) {
		window.location.href = getPhotoUrl(photo_pk);
	})
	fullscreenContainer.append(newWrapper);
}

// Swipe left -> next image
function navigateToNext() {
	const newCurrentImageIdx = fullscreenContainer.data('current-image-idx') + 1;
	if (newCurrentImageIdx > $photos_count) {
		return  // no next image
	}
	// Update the current image ID and preload adjacent images
	fullscreenContainer.data('current-image-idx', newCurrentImageIdx);
	// swipe left
	$('.image-wrapper.current').css('transform', 'translateX(-100%)');
	$('.image-wrapper.next').css('transform', 'translateX(0)');
	// the prev is removed and replaced by the current
	$('.image-wrapper.prev').remove();
	$('.image-wrapper.current').removeClass('current').addClass('prev');
	// the next becomes the current
	$('.image-wrapper.next').removeClass('next').addClass('current');
	// the next must be created: preload the new next image and create the new next wrapper
	if (newCurrentImageIdx >= $photos_count) {
		return  // no next image
	}
	$.ajax({
		url: getImageUrl(newCurrentImageIdx + 1),
		method: 'GET',
		success: function(response) {
			createNewWrapper('next', 'translateX(100%)', response.image_url, response.pk)
		}
	});
}

// Swipe right -> previous image
function navigateToPrevious() {
	const newCurrentImageIdx = fullscreenContainer.data('current-image-idx') - 1;
	if (newCurrentImageIdx < 1) {
		return  // no previous image
	}
	// Update the current image ID
	fullscreenContainer.data('current-image-idx', newCurrentImageIdx);
	// swipe right
	$('.image-wrapper.current').css('transform', 'translateX(100%)');
	$('.image-wrapper.prev').css('transform', 'translateX(0)');
	// the next is removed and replaced by the current
	$('.image-wrapper.next').remove();
	$('.image-wrapper.current').removeClass('current').addClass('next');
	// the prev becomes the current
	$('.image-wrapper.prev').removeClass('prev').addClass('current');
	// the prev must be created: preload the new prev image and create the new prev wrapper
	if (newCurrentImageIdx <= 1) {
		return  // no previous image
	}
	$.ajax({
		url: getImageUrl(newCurrentImageIdx - 1),
		method: 'GET',
		success: function(response) {
			createNewWrapper('prev', 'translateX(-100%)', response.image_url, response.pk)
		}
	});
}

$(document).ready(function() {
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
	$('.gallery-image').click(function() {
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
