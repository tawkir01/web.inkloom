# Inkloom Guardian frontend

The public experience is served at `/` and is a frontend-only demonstration. All displayed brands, metrics, review records, evidence, and audit history are illustrative. The content checker runs local simulated rules; it does not call an AI provider or save submitted text.

## Development

From this directory:

```sh
npm install
npm run dev
```

For a production bundle, run `npm run build`.

## Authenticated workspace

The existing workspace views remain in the application and require a validated authenticated session. There is currently no dedicated, published sign-in route for workspace access. Add and security-test an authorized route before exposing those modules as a separate user flow. Do not remove the backend's authenticated permissions, workspace membership checks, role checks, or tenant isolation. Auth tokens are scoped to the current browser session in `sessionStorage`.
