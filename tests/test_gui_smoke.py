"""Offscreen Qt smoke test: every existing page and new control constructs."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest
from PySide6.QtWidgets import QApplication

from ui.main_window import ManagerWindow


class MainWindowSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_all_pages_and_new_tools_are_present(self):
        window = ManagerWindow()
        try:
            self.assertEqual(window.pages.count(), 6)
            self.assertEqual(len(window.nav_buttons), 6)
            self.assertIsNotNone(window.sights_page)
            self.assertIsNotNone(window.camouflages_page)
            self.assertIsNotNone(window.sounds_page)
            self.assertIsNotNone(window.settings_page)
            self.assertIsNotNone(window.online_page)
            self.assertTrue(hasattr(window.sounds_page, "audio_waveform"))
            self.assertTrue(hasattr(window.sounds_page, "repeat_button"))
            self.assertTrue(hasattr(window.sounds_page, "sound_search"))
            self.assertTrue(hasattr(window.online_page, "catalog_list"))
            self.assertTrue(hasattr(window.online_page, "profile_picker"))
            self.assertTrue(hasattr(window.online_page, "update_button"))
            self.assertTrue(hasattr(window.online_page, "rollback_exe_button"))
            self.assertTrue(hasattr(window.online_page, "remote_notifications"))
            self.assertTrue(hasattr(window.online_page, "diagnostic_scan"))
            self.assertEqual(window.online_page.tabs.count(), 3)
            self.assertIsNotNone(window.online_page.security_panel)
            self.assertTrue(hasattr(window.online_page.security_panel, "choose_button"))
            self.assertTrue(hasattr(window.online_page.security_panel, "lookup_button"))
            self.assertIsNotNone(window.online_page.trust_panel)
            self.assertIsNotNone(window.online_page.mod_tools_panel)
            self.assertIsNotNone(window.online_page.offline_switch)
            self.assertIsNotNone(window.online_page.early_beta_checkbox)
            self.assertIsNotNone(window.online_page.diagnostic_repair)
            self.assertIsNotNone(window.settings_page.setting_search)
            self.assertIsNotNone(window.online_page.channel_picker)
            self.assertIsNotNone(window.online_page.remote_notifications)
            self.assertIsNotNone(window.online_page.updates_inbox)
            self.assertIsNotNone(window.online_page.update_progress)
            self.assertIsNotNone(window.online_page.update_progress_note)
            window.online_page.begin_update_download()
            self.assertTrue(window.online_page.update_progress.isVisibleTo(window.online_page))
            window.online_page.set_update_download_progress(57)
            self.assertEqual(window.online_page.update_progress.value(), 57)
            window.online_page.finish_update_download(False)
            self.assertFalse(window.online_page.update_progress.isVisibleTo(window.online_page))
        finally:
            window.online_page.bridge.stop()
            window.force_close()


if __name__ == "__main__":
    unittest.main()
