# WT Mod Manager — Beta 12: Reliability, Trust & Safe Mod Scanning

## WT Recovery / Crash Reporter

- Local crash report saves only exception **type**, function names and line
  numbers. It intentionally excludes exception messages, paths, tokens,
  filenames, source code, Windows usernames, and mod contents.
- The 8 most recent crash reports are kept under the Windows user's
  `%LOCALAPPDATA%\WTModManager\recovery\crashes`.
- Reports are never transmitted automatically. The user can copy a redacted
  report from **Загрузки → Диагностика → WT Trust Center**.
- A post-update crash/forced shutdown triggers a recovery **suggestion** on
  next launch; a forced restart is not proof that the new version is broken.
- Existing verified portable rollback remains available with the user's
  explicit confirmation. Installed builds continue to use Inno Setup and
  don't silently overwrite Windows installer registrations.

## Smart Update and Release Channels

- Staged downloads check sufficient free space and reject symlinked
  update-cache paths before reaching the network.
- Downloaded updates must match GitHub's release asset size and SHA-256.
- Stable/Beta can now be selected from **Загрузки** without reinstalling.
- Stable is only selected when GitHub marks the release as non-prerelease.
  The Beta 12 binary is **not** silently promoted to Stable.
- We never auto-downgrade, silently install an update, or disable SmartScreen.

## WT Trust Center

- The app checks the *local* executable's SHA-256 and Windows Authenticode
  status on demand, without any upload.
- The site has `docs/trust.html` to list public GitHub Release metadata,
  checksum links and build provenance.
- GitHub Sigstore attestations verify the origin of release artifacts, not
  their absence of malware; real Windows publisher signing requires an
  Authenticode certificate. Users should not bypass OS security warnings.

## Vulnerability Reports and Software Bill of Materials

- Dependabot checks Python pinned build requirements and GitHub Actions.
- A separate GitHub workflow runs PyPA `pip-audit` weekly and when pinned
  dependencies change. Any reported issue must be reviewed before merging
  that dependency update.
- The build produces a CycloneDX-format Python package inventory
  `sbom.cdx.json` from the actual build environment.
- SBOM is published with the installer, recorded by GitHub provenance
  attestation, and verified during the protected publish stage.
- The older `release-checksums.yml` workflow no longer overwrites
  `SHA256SUMS.txt` on already-published releases. It checks it read-only.

## WT Mod Scanner

- One-at-a-time ZIP processing and structural checks are unchanged.
- A private 30-day SHA-256 cache stores only successful structural
  **checked** / **review** verdicts from the same scanner version.
  No antivirus clearance is cached. The scanner ruleset version changes
  whenever inspection behavior changes.
- SQL queue priorities are server-managed (0–2) and have an age bonus,
  so older submissions gain priority instead of starving indefinitely.
- Temporary errors use bounded backoff; 3 attempts remain the maximum.
- The public catalogue explains CRC/size findings and distinguishes
  structural checks from antivirus findings.
- **All mods still require manual moderation.** ClamAV is a separate optional
  pipeline and is not made permanently active by these ZIP enhancements.

## Limitations and release readiness

- Some features are intentionally consent-based rather than fully automatic:
  rollback and crash-report sharing never happen without user permission.
- The signed publisher certificate has not been provided. Beta builds can
  remain unsigned despite verified GitHub provenance, and SmartScreen can
  continue warning.
- A local crash log cannot reliably determine *why* Windows terminated a
  process; unclean exits are prompts to inspect the app, not proof of malware.
- The server scanner cache must be deployed **after** its SQL migration.
- Automated tests cannot substitute for a complete live ZIP upload and
  Windows desktop manual review.
