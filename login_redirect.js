// Failsafe: redirect logged-in users away from the login page to /helpdesk
(function () {
	if (window.location.pathname !== "/login") return;

	// Check if user is logged in (frappe sets this cookie after login)
	var sid = (document.cookie.match(/sid=([^;]+)/) || [])[1];
	if (!sid || sid === "Guest") return;

	// Give the normal login.js redirect a moment to work, then force it
	setTimeout(function () {
		if (window.location.pathname === "/login") {
			var redirectTo =
				new URLSearchParams(window.location.search).get("redirect-to") ||
				"/helpdesk";
			window.location.replace(redirectTo);
		}
	}, 1500);
})();

// Show build version badge on the login page
(function () {
	if (window.location.pathname !== "/login") return;
	function injectVersion() {
		var badge = document.createElement("div");
		badge.style.cssText =
			"position:fixed;bottom:12px;right:16px;font-size:11px;" +
			"color:#aaa;font-family:monospace;letter-spacing:.5px;z-index:9999;";
		badge.textContent = "v__APP_VERSION__";
		document.body.appendChild(badge);
	}
	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", injectVersion);
	} else {
		injectVersion();
	}
})();
