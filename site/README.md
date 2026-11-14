# PhishLens landing page

This is a static landing page for Vercel. It is separate from the Chrome extension
and the FastAPI backend; it does not host either runtime.

## Deploy with Vercel

1. Push this branch to the GitHub repository.
2. In Vercel, choose **Add New → Project** and import the PhishLens repository.
3. Set **Root Directory** to `site`.
4. Select **Other** as the framework preset. Leave Build Command and Output
   Directory empty; Vercel will serve `index.html` as a static site.
5. Deploy. Vercel will create preview deployments for branches and deploy the
   production branch when configured in Project Settings → Git.

The Login and Sign up dialogs are presentation-only until an authentication
provider and a backend account API are configured. They deliberately do not
submit the entered credentials to a service or save them.

The side panel runs inside Chrome as part of the extension and cannot be hosted
by Vercel. Package and install the extension separately; this page describes it.
