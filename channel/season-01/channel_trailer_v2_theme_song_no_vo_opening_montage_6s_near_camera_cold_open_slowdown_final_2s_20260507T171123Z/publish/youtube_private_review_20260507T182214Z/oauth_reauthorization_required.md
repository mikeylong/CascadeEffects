# YouTube OAuth Reauthorization Required

The private upload packet is ready, but API upload is currently blocked:

- `status`: `blocked`
- `reason`: local YouTube OAuth refresh token is expired or revoked
- `required_scopes`: `youtube.readonly`, `youtube.upload`
- `credential_dir`: `/Users/mike/.config/cascade-effects/youtube`

Use the existing Google OAuth client in that directory to refresh `access_token.json`, then rerun the private upload with the payload in this packet.

Public release remains manual in YouTube Studio after processing, copyright, Content ID, altered-content, audience, thumbnail, and visibility checks.
