// Function to open image or video in full screen
function openFullscreen(imageElement) {
  const swipeUrl = imageElement.data("swipe-url");
  // Trigger HTMX to load the initial image or video content
  htmx.ajax("GET", swipeUrl + "#image", {
    target: "#swipe-container",
  });

  $("#fullscreen-overlay") // display the overlay
    .css("display", "flex")
    .hide()
    .fadeIn(300);

  syncFullscreenButton();
}
// Function to swipe an image or a video
function executeSwipe(side, diff = null) {
  const container = $("#image-container");
  const url = container.attr("hx-get");
  const angle = diff ? -diff / 15 : side === "prev" ? -60 : 60;
  const sign = side === "prev" ? "-" : "";
  if (url) {
    container.css({
      transform: `translateX(${sign}150%) rotate(${angle}deg)`,
      opacity: "0",
    });
    htmx.ajax("GET", url, {
      target: "#swipe-container",
      values: { side: side },
    });
  }
}

// Close full screen
function closeFullScreen() {
  fullscreenContainer = $("#fullscreen-overlay");
  fullscreenContainer.fadeOut(300);
  fullscreenContainer.find("#image-container").html("");
}

// slide show functions

function startSlideshowTimer(slideshowTimer = null) {
  // Clear any existing timer
  if (slideshowTimer) {
    clearTimeout(slideshowTimer);
  }
  const slideshowDelay =
    (parseInt($("#slideshow-toggle").data("delay")) || 5) * 1000;
  return setTimeout(function () {
    executeSwipe("next");
  }, slideshowDelay);
}

function toggleSlideshow(slideshowTimer = null) {
  const btn = $("#slideshow-toggle");
  const icon = $("#slideshow-icon");
  const fullscreenBtn = $("#fullscreen-slideshow-toggle");
  const fullscreenIcon = $("#fullscreen-slideshow-icon");
  const isActive = btn.hasClass("is-active");

  if (isActive) {
    // Stop slideshow
    btn.removeClass("is-active");
    icon.removeClass("mdi-pause").addClass("mdi-play");
    fullscreenBtn.removeClass("is-active");
    fullscreenIcon.removeClass("mdi-pause").addClass("mdi-play");
    if (slideshowTimer) {
      clearTimeout(slideshowTimer);
    }
    return null;
  } else {
    // Start slideshow
    btn.addClass("is-active");
    icon.removeClass("mdi-play").addClass("mdi-pause");
    fullscreenBtn.addClass("is-active");
    fullscreenIcon.removeClass("mdi-play").addClass("mdi-pause");

    // If not already in fullscreen, open the first image
    if ($("#fullscreen-overlay").css("display") === "none") {
      const firstImage = $(".gallery-image").first();
      if (firstImage.length > 0) {
        openFullscreen(firstImage);
      }
    }
    return startSlideshowTimer(slideshowTimer);
  }
}

// Initial state for fullscreen slideshow button when opening fullscreen
function syncFullscreenButton() {
  const isActive = $("#slideshow-toggle").hasClass("is-active");
  const fullscreenIcon = $("#fullscreen-slideshow-icon");
  const fullscreenBtn = $("#fullscreen-slideshow-toggle");

  if (isActive) {
    fullscreenBtn.addClass("is-active");
    fullscreenIcon.removeClass("mdi-play").addClass("mdi-pause");
  } else {
    fullscreenBtn.removeClass("is-active");
    fullscreenIcon.removeClass("mdi-pause").addClass("mdi-play");
  }
}

$(document).ready(function () {
  // Variables to store touch start and current positions for swiping
  let startX = 0;
  const minSwipeDistance = 120; // Minimum distance to detect a swipe

  // Touch event manager functions for swipe left/right on a card
  $(document).on("touchstart", "#image-container", function (e) {
    startX = e.originalEvent.touches[0].pageX;
    // Disable transition during swipe
    $(this).css("transition", "none");
  });

  $(document).on("touchmove", "#image-container", function (e) {
    // Calculate displacement in real time
    const currentX = e.originalEvent.touches[0].pageX;
    let diff = currentX - startX;
    // Rotation and displacement, divide the rotation for a more natural effect
    $(this).css("transform", `translateX(${diff}px) rotate(${diff / 15}deg)`);
  });

  $(document).on("touchend", "#image-container", function (e) {
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
      $(this).css("transform", "translateX(0) rotate(0)");
    }

    startX = 0;
  });

  // Open image in full screen
  $(document).on("click", ".gallery-image", function () {
    openFullscreen($(this));
  });

  // Navigate to previous image
  $(document).on("click", "#prev-image", function () {
    // console.log("prev-image");
    setTimeout(() => executeSwipe("prev"), 20);
  });

  // Navigate to next image
  $(document).on("click", "#next-image", function () {
    // console.log("next-image");
    setTimeout(() => executeSwipe("next"), 20);
  });

  $(document).on("click", "#close-fullscreen", closeFullScreen);

  // Close full screen if clicked outside image
  $(document).on("click", "#image-container", function (e) {
    if (e.target === e.currentTarget) {
      closeFullScreen();
    }
  });

  // Open image in full screen if URL parameter is present
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("openFullscreen") === "true") {
    openFullscreen(
      $(`.gallery-image[data-fullscreen="${urlParams.get("firstImage")}"]`),
    );
  }

  // Slideshow logic
  let slideshowTimer = null;

  $("#slideshow-toggle, #fullscreen-slideshow-toggle").click(function (e) {
    e.stopPropagation(); // Prevent closing fullscreen
    slideshowTimer = toggleSlideshow(slideshowTimer);
  });

  // Automatically move to the next slide when content is loaded, if slideshow is active
  $(document).on("htmx:afterOnLoad", function (evt) {
    if (
      evt.detail.target.id === "swipe-container" &&
      $("#slideshow-toggle").hasClass("is-active")
    ) {
      slideshowTimer = startSlideshowTimer(slideshowTimer);
    }
  });

  // Reset timer on manual navigation
  $(document).on("click", "#prev-image, #next-image", function () {
    if ($("#slideshow-toggle").hasClass("is-active")) {
      slideshowTimer = startSlideshowTimer(slideshowTimer);
    }
  });

  // Stop slideshow when fullscreen is closed
  $(document).on("click", "#close-fullscreen", function () {
    if ($("#slideshow-toggle").hasClass("is-active")) {
      slideshowTimer = toggleSlideshow(slideshowTimer);
    }
  });
});
