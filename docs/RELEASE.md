# Releases & Docker image versioning 🔖

This repository uses Git tags (semantic version tags starting with `v`, e.g. `v1.2.3`) to create releases. The Docker images are the primary released artifact and are published to GitHub Container Registry (GHCR) when a tag is pushed.

How it works:

- Create a new release tag locally: `./scripts/release.sh v1.2.3` (this will create an annotated tag and push it).
- Pushing the tag triggers `.github/workflows/release.yml`:
  - Builds backend and frontend Docker images
  - Tags them as `ghcr.io/<owner>/mealplanner-backend:<TAG>` and `.../mealplanner-frontend:<TAG>` and also as `...:latest`
  - Pushes images to GHCR
  - Creates a GitHub Release with basic notes and recent commits

Pulling the images:

- Authenticate with GHCR: `echo $GITHUB_TOKEN | docker login ghcr.io -u <USERNAME> --password-stdin`
- Pull an image: `docker pull ghcr.io/<owner>/mealplanner-backend:v1.2.3`

Notes:

- The release workflow runs only on tags matching `v*` (semantic `vMAJOR.MINOR.PATCH`).
- Make sure `GITHUB_TOKEN` has the `packages:write` permission (the workflow sets this permission automatically for itself).
- You can also create releases using the GitHub UI; pushing a tag still triggers the workflow and will publish images.

Automatic changelog drafts:

- We use Release Drafter to assemble merged PRs into a draft release on `main`. When PRs are merged, a draft changelog is updated automatically with categorized entries (Added, Changed, Fixed, etc.). When you're ready to ship, create a semantic tag (`./scripts/release.sh v1.2.3`) to publish the images and convert the draft into a published GitHub Release.
