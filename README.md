# devops_action_release

## Overview

This repository provides a streamlined method for releasing GitHub repositories. The release process includes:

- Merging a source branch (typically `main`) into a release branch (usually formatted as `v*`, e.g., `v0`).
- Bumping the version based on commit history, adhering to the conventional commit format.
- Generating a CHANGELOG from conventional commit messages.
- Tagging the latest commit in the release branch with a release tag (e.g., `v0.1.0`).

## Repository Components

- `action.yaml`: Wraps the releaser Python package as composite action and passes commands.

## Branch Structure Example

Here is an example branch structure from the tests (`tests/resources/changelog_v100.md`):

```txt
* Update CHANGELOG for v1.0.0 (HEAD -> v1, tag: v1.0.0, origin/v1)
*   Merge `main` into `v1`
|\
| * feat!: breaking change (origin/main)
* | Update CHANGELOG for v0.1.1 (tag: v0.1.1, origin/v0)
* | Merge `main` into `v0`
|\|
| * fix: resolve a bug
* | Update CHANGELOG for v0.1.0 (tag: v0.1.0)
* | Merge `main` into `v0`
|\|
| * feat: add a new feature
|/
* first commit
```

## Usage

To integrate this release action into your repository, use the following configuration in your GitHub Actions workflow. Replace `<version>` with the appropriate version of the workflow you want to use:

### Release

This setup triggers the release process whenever changes are pushed to the `main` branch.

```yaml
---
name: Release

on:
  push:
    branches:
      - main

jobs:
  release:
    uses: kobo-labs/releaser/.github/workflows/release.yml@<version>
    secrets: inherit
```

### Check

This setup triggers the commit message check for pull requests to the `main` branch.

```yaml
---
name: Check

on:
  pull_request:
    branches:
      - main

jobs:
  release:
    uses: kobo-labs/releaser/.github/workflows/check.yml@<version>
    secrets: inherit
```

### How to Create a GitHub App for Branch Protection

To ensure the release branch is protected during the release process, follow these steps to create and configure a GitHub App:

1. **Create a New GitHub App**:
   - Navigate to your organization's GitHub settings.
   - Go to **Developer settings** -> **GitHub Apps**.
   - Click **New GitHub App** and fill in the required fields such as the app's name, homepage URL, and callback URL (you can leave this blank if not required).
2. **Set Permissions for the GitHub App**:
   Configure the necessary permissions for the app:

   - **Actions**: `Read and write` – Allows the app to manage workflows and their runs.
   - **Administration**: `Read and write` – Enables the app to configure and manage repository settings like branch protection.
   - **Contents**: `Read and write` – Grants access to create, read, update, and delete repository contents, including tags and releases.
   - **Metadata**: `Read-only` – Allows the app to access repository information, such as the list of branches and collaborators.

3. **Generate and Store the Private Key**:

   - After setting up permissions, generate a **Private Key** for the GitHub App by navigating to the app's settings page.
   - Download the generated private key and store it securely. You'll need this key to authenticate your app.

4. **Install the GitHub App on Your Organization**:

   - Once the app is created, go to **App Settings** -> **Install App**.
   - Select **All repositories** or choose specific repositories where the app should be installed.

5. **Configure Secrets and Environment Variables**:
   - Add the private key to your repository as a **Secret** (e.g., `APP_PRIVATE_KEY`).
   - Add the **App ID** as a repository **Environment Variable** (e.g., `APP_ID`).
6. **Set Up Branch Protection Rules**:
   - Go to your repository settings and navigate to **Branches** -> **Branch protection rules**.
   - Create a new rule to protect the release branch (e.g., `v*`).
   - Ensure the protection rule requires all changes to go through the GitHub App by selecting **Require status checks to pass before merging** and adding relevant checks (e.g., the `release` job).
