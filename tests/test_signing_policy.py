"""Offline Authenticode policy checks: never load owner credentials or keys."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AuthenticodeReleasePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = (ROOT / "tools" / "sign_windows_release.ps1").read_text("utf-8")
        cls.workflow = (ROOT / ".github" / "workflows" /
                        "build-windows-exe.yml").read_text("utf-8")

    def test_three_real_binary_stages_and_sha256_timestamp(self):
        for value in ('"native", "payload", "installer"',
                      'build\\wtmm_taskbar.dll',
                      'dist\\WTModManager.exe',
                      'dist\\WTModManager-Setup.exe'):
            self.assertIn(value, self.script)
        for term in ('/fd SHA256', '/td SHA256', 'verify /pa /v',
                     'Get-AuthenticodeSignature', "Status -ne 'Valid'"):
            self.assertIn(term, self.script)

    def test_required_signing_refuses_missing_owner_key(self):
        self.assertIn('$env:WTMM_REQUIRE_AUTHENTICODE -eq "true"', self.script)
        self.assertIn('if ($requireSignature)', self.script)
        self.assertIn('no publisher certificate was configured', self.script)
        self.assertIn('WTMM_SIGN_CERT_THUMBPRINT', self.script)
        self.assertIn("^[A-F0-9]{40}$", self.script)
        self.assertIn('$actualThumbprint -ne $expectedThumbprint', self.script)
        self.assertNotIn('New-SelfSignedCertificate', self.script)

    def test_owner_private_key_is_temporary_and_not_in_repository(self):
        self.assertIn('$env:WTMM_SIGN_PFX_BASE64', self.script)
        self.assertIn('$env:WTMM_SIGN_PFX_PASSWORD', self.script)
        self.assertIn('Join-Path $env:RUNNER_TEMP', self.script)
        self.assertIn('Remove-Item -LiteralPath $privateKeyPath', self.script)
        self.assertNotIn('Write-Output $password', self.script)
        self.assertNotIn('Write-Output $encoded', self.script)

    def test_secrets_are_only_in_main_trusted_signing_steps(self):
        self.assertEqual(
            self.workflow.count('WTMM_SIGN_PFX_BASE64: ${{ secrets.WTMM_SIGN_PFX_BASE64 }}'),
            3
        )
        self.assertEqual(
            self.workflow.count("if: github.event_name == 'push' && github.ref == 'refs/heads/main'"),
            5
        )
        self.assertEqual(
            self.workflow.count('WTMM_SIGN_CERT_THUMBPRINT: ${{ vars.WTMM_SIGN_CERT_THUMBPRINT }}'),
            3
        )
        self.assertIn(
            'if ($env:WTMM_REQUIRE_AUTHENTICODE -eq \'true\' -and $valid.Count -ne 2)',
            self.workflow
        )
        self.assertIn("both trusted and signed", self.workflow)


if __name__ == "__main__":
    unittest.main()
