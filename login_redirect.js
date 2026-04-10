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
