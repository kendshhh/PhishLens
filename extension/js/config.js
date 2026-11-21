export const API_BASE_URLS = Object.freeze({
    production: "https://phishlens-api-ocvt.onrender.com",
    staging: "https://phishlens-staging.onrender.com",
});

// The release package defaults to production. Staging acceptance selects the
// isolated service through the extension page's internal environment query.
export const API_BASE_URL = API_BASE_URLS.production;
