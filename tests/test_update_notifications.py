"""Windows-local update notification tests (no internet or real EXE changes)."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication

from src import update_notifications as events
from ui.update_ui import UpdateController, CHECK_INTERVAL_MS


class UpdateNotificationTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "update-notifications.json"
        mock = patch("src.update_notifications.NOTIFICATIONS_FILE", self.path)
        mock.start()
        self.addCleanup(mock.stop)

    def test_duplicate_release_creates_only_one_notification(self):
        self.assertTrue(events.record_event(
            "update_available", "Новое обновление", "Описание", "v1.4.0",
            "update-available:v1.4.0"
        ))
        self.assertFalse(events.record_event(
            "update_available", "Новое обновление", "Описание", "v1.4.0",
            "update-available:v1.4.0"
        ))
        self.assertEqual(len(events.load_notifications()["events"]), 1)

    def test_prefs_persist_across_restarts(self):
        events.set_auto_check(False)
        events.ignore_version("v1.4.0")
        state = events.load_notifications()
        self.assertFalse(state["auto_check"])
        self.assertEqual(state["ignored_version"], "v1.4.0")

    def test_mark_all_read_does_not_remove_history(self):
        events.record_event("update_ready", "Загружено", "Можно установить", "v1.4.0")
        events.mark_all_read()
        self.assertEqual(len(events.load_notifications()["events"]), 1)
        self.assertTrue(events.load_notifications()["events"][0]["read"])

    def test_history_is_bounded(self):
        for number in range(80):
            events.record_event(
                "notice", "Event " + str(number), "Text", event_id=str(number)
            )
        state = events.load_notifications()
        self.assertEqual(len(state["events"]), events.MAX_EVENTS)
        self.assertEqual(state["events"][-1]["title"], "Event 79")

    def test_invalid_json_returns_safe_defaults(self):
        self.path.write_text("{not JSON", encoding="utf-8")
        self.assertEqual(events.load_notifications()["events"], [])
        self.assertTrue(events.load_notifications()["auto_check"])

    def test_after_restart_records_update_status(self):
        with tempfile.TemporaryDirectory() as folder:
            update_dir = Path(folder) / "updates"
            update_dir.mkdir()
            status = update_dir / "last-update-status.txt"
            status.write_text("Обновление установлено. Приложение запущено.",encoding="utf-8")
            with patch("src.update_notifications.DATA_DIR", Path(folder)):
                message = events.consume_install_status()
            self.assertIn("Обновление установлено", message)
            self.assertFalse(status.exists())
            self.assertEqual(events.load_notifications()["events"][-1]["kind"],
                             "update_installed")


class UpdateControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        p = patch("src.update_notifications.NOTIFICATIONS_FILE",
                  Path(self.folder.name) / "notices.json")
        p.start()
        self.addCleanup(p.stop)
        self.controller = UpdateController()
        self.addCleanup(self.controller._timer.stop)

    def test_automatic_check_interval(self):
        self.assertEqual(self.controller._timer.interval(), CHECK_INTERVAL_MS)
        self.assertEqual(CHECK_INTERVAL_MS, 600000)

    def test_new_release_emits_notification_once(self):
        arrivals = []
        tray = []
        self.controller.update_available.connect(arrivals.append)
        self.controller.tray_notification.connect(lambda title,message:tray.append(message))
        info = {"version": "v1.4.0", "digest": "a"*64}
        self.controller._finished(info, "", downloaded=False)
        self.controller._finished(info, "", downloaded=False)
        self.assertEqual(len(arrivals), 2)
        self.assertEqual(len(tray), 1)
        self.assertEqual(len(events.load_notifications()["events"]), 1)
        self.assertEqual(self.controller.current_update["version"],"v1.4.0")

    def test_ignored_version_never_emits_tray_alert(self):
        events.ignore_version("v1.4.0")
        seen = []
        self.controller.tray_notification.connect(lambda *args:seen.append(args))
        self.controller._finished({"version":"v1.4.0"}, "", downloaded=False)
        self.assertFalse(seen)

    def test_disabled_auto_does_not_start_network_check(self):
        events.set_auto_check(False)
        with patch.object(self.controller,"_start") as start:
            self.controller.check()
        start.assert_not_called()


if __name__ == "__main__":
    unittest.main()
