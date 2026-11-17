// WT Mod Manager: UI gate for human moderation of submitted archives.
// This prevents accidental approval through the normal interface.
// It is NOT a security boundary; server-side authorization and scanning are still required.
export function modReviewReady(archiveValidated, manualReviewOpened) {
    return archiveValidated === true && manualReviewOpened === true;
}
