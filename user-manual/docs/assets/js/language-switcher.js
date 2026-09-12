// Language switcher for Read the Docs translations model.
// Each language is a separate RTD project served under /{lang}/{version}/,
// so switching language = swapping the first path segment of the current URL.
(function () {
  "use strict";

  var LANGS = [
    ["en", "English"],
    ["fr", "Français"],
    ["es", "Español"],
    ["de", "Deutsch"],
    ["it", "Italiano"],
    ["pt", "Português"],
  ];

  var m = location.pathname.match(/^\/([a-z]{2})(?=\/|$)/);
  var current = m ? m[1] : "en";

  function urlFor(lang) {
    if (m) {
      return location.pathname.replace(/^\/[a-z]{2}(?=\/|$)/, "/" + lang) + location.hash;
    }
    return "/" + lang + "/";
  }

  function render(container, inline) {
    var div = document.createElement("div");
    div.className = "cm-langs" + (inline ? " cm-langs-inline" : "");
    LANGS.forEach(function (pair, i) {
      if (i > 0) {
        div.appendChild(document.createTextNode(inline ? " | " : " · "));
      }
      var a = document.createElement("a");
      a.href = urlFor(pair[0]);
      a.textContent = pair[1];
      if (pair[0] === current) {
        a.className = "cm-langs-current";
        a.setAttribute("aria-current", "true");
      }
      div.appendChild(a);
    });
    container.appendChild(div);
  }

  function inject() {
    var style = document.createElement("style");
    style.textContent =
      ".cm-langs{font-size:80%;padding:12px 0 4px;text-align:center}" +
      ".cm-langs a{color:#bbb;text-decoration:none}" +
      ".cm-langs a.cm-langs-current{color:#fff;font-weight:bold;text-decoration:underline}" +
      ".cm-langs-inline{display:inline-block;padding:0 12px;font-size:70%;color:#fff}" +
      ".cm-langs-inline a{color:#fff}" +
      ".cm-langs-inline a.cm-langs-current{text-decoration:underline}";
    document.head.appendChild(style);

    var side = document.querySelector(".wy-side-nav-search");
    if (side) { render(side, false); }
    var top = document.querySelector(".wy-nav-top");
    if (top) { render(top, true); }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inject);
  } else {
    inject();
  }
})();
