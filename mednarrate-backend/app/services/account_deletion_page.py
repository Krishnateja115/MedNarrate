"""Public, same-origin account deletion page for the future Play listing."""

import secrets

from fastapi.responses import HTMLResponse


_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Delete your MedNarrate account</title>
  <style>
    body { font: 16px/1.5 system-ui, sans-serif; background: #fff; color: #13241f; margin: 0; }
    main { max-width: 520px; margin: 6vh auto; padding: 24px; }
    h1 { line-height: 1.2; }
    label { display: block; margin-top: 18px; font-weight: 600; }
    input { display: block; width: 100%; box-sizing: border-box; padding: 12px; margin-top: 6px; border: 1px solid #9bada8; border-radius: 8px; font: inherit; }
    button { margin-top: 24px; padding: 12px 18px; border: 0; border-radius: 8px; background: #a22121; color: white; font: inherit; cursor: pointer; }
    button:disabled { opacity: .5; cursor: wait; }
    #status { min-height: 2em; margin-top: 16px; }
  </style>
</head>
<body>
<main>
  <h1>Delete your MedNarrate account</h1>
  <p>You can also delete your account in the MedNarrate app under Settings. This page works without the app.</p>
  <p>Deletion removes your uploaded reports, medical profile, reminders, chat history and account access. Save an archive from the app first if you need one. This action cannot be undone.</p>
  <form id="delete-form">
    <label for="email">Account email</label>
    <input id="email" type="email" autocomplete="username" required>
    <label for="password">Password</label>
    <input id="password" type="password" autocomplete="current-password" required>
    <button type="submit">Permanently delete my account</button>
  </form>
  <p id="status" role="status" aria-live="polite"></p>
</main>
<script nonce="__NONCE__">
  document.getElementById('delete-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector('button');
    const status = document.getElementById('status');
    const email = document.getElementById('email').value.trim();
    const passwordField = document.getElementById('password');
    const password = passwordField.value;
    if (!confirm('Permanently delete this account and its medical data?')) return;
    button.disabled = true;
    status.textContent = 'Verifying your account…';
    try {
      const login = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: new URLSearchParams({username: email, password}),
        cache: 'no-store'
      });
      if (!login.ok) throw new Error('Could not verify the email and password.');
      const credentials = await login.json();
      if (!credentials.access_token) throw new Error('Please complete account verification in the app.');
      status.textContent = 'Deleting your account…';
      const deleted = await fetch('/api/v1/users/me', {
        method: 'DELETE',
        headers: {
          'Authorization': 'Bearer ' + credentials.access_token,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({password}),
        cache: 'no-store'
      });
      if (!deleted.ok) throw new Error('Deletion failed. Please try again or use the app.');
      form.reset();
      form.hidden = true;
      status.textContent = 'Your MedNarrate account has been deleted.';
    } catch (error) {
      status.textContent = error.message;
    } finally {
      passwordField.value = '';
      button.disabled = false;
    }
  });
</script>
</body>
</html>"""


def account_deletion_page() -> HTMLResponse:
    """Return a no-store page that calls existing rate-limited login and deletion APIs."""
    nonce = secrets.token_urlsafe(24)
    return HTMLResponse(
        _PAGE.replace("__NONCE__", nonce),
        headers={
            "Cache-Control": "no-store",
            "Content-Security-Policy": (
                "default-src 'none'; "
                f"script-src 'nonce-{nonce}'; "
                "style-src 'unsafe-inline'; connect-src 'self'; "
                "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
            ),
        },
    )
