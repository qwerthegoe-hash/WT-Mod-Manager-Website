"""Non-network tests for the twelve WT Mod Suite safety features."""
from __future__ import annotations
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.game_mod_installer import CopyPlan, InstallError
from src import mod_suite, offline_mode, release_rollout, diagnostics, update_checker


class ModSuiteTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        self.source=self.root / "new.blk"
        self.source.write_bytes(b"new data")
        self.dst=self.root / "game" / "new.blk"
        self.dst.parent.mkdir()
        self.dst.write_bytes(b"old data")

    def test_conflict_preview_is_readonly(self):
        row=CopyPlan(self.source,self.dst,True,False)
        preview=mod_suite.preview_install([row])
        self.assertEqual(preview.replacements,1)
        self.assertGreater(preview.required_space,0)
        self.assertEqual(preview.conflicting_filenames,("new.blk",))
        self.assertEqual(self.dst.read_bytes(),b"old data")
        self.assertEqual(mod_suite.resolve_conflicts([row],"keep"),[])
        self.assertEqual(mod_suite.resolve_conflicts([row],"replace"),[row])
        self.assertEqual(mod_suite.resolve_conflicts([row],"cancel"),[])
        with self.assertRaisesRegex(InstallError,"Недостаточно"):
            mod_suite.preview_install([row],available_bytes=0)

    def test_no_duplicate_destinations(self):
        item=CopyPlan(self.source,self.dst,True,False)
        with self.assertRaises(InstallError):
            mod_suite.preview_install([item,item])

    def test_history_has_no_paths_or_tokens(self):
        path=self.root / "history.json"
        with patch.object(mod_suite,"TIMELINE_PATH",path):
            mod_suite.append_history("installed","a"*32,1)
            mod_suite.append_history("restored","a"*32,1)
            hist=mod_suite.history()
        self.assertEqual([x["event"] for x in hist],["installed","restored"])
        self.assertNotIn(str(self.root),path.read_text("utf-8"))

    def test_integrity_detects_manual_modification(self):
        folder=self.root / "backups" / ("b"*32)
        folder.mkdir(parents=True)
        digest=hashlib.sha256(self.dst.read_bytes()).hexdigest()
        (folder / "manifest.json").write_text(json.dumps({
            "files":[{"target":str(self.dst),"installed_digest":digest}]
        }),"utf-8")
        with patch.object(mod_suite,"REGISTRY_DIR",self.root / "backups"):
            self.assertEqual(mod_suite.installed_integrity()[0]["status"],"ok")
            self.dst.write_bytes(b"changed")
            self.assertEqual(mod_suite.installed_integrity()[0]["status"],"changed")

    def test_compatibility_is_not_invented(self):
        self.assertEqual(mod_suite.compatibility({},"2.45.0")["status"],"unknown")
        self.assertEqual(mod_suite.compatibility(
            {"game_version":"2.45.0"},"2.45.0")["status"],"match")
        self.assertEqual(mod_suite.compatibility(
            {"game_version":"2.45.0"},"2.44.0")["status"],"review")

    def test_modpack_is_manifest_only(self):
        account=self.root / "account"
        account.mkdir()
        uuid="c"*8+"-"+"d"*4+"-"+"e"*4+"-"+"f"*4+"-"+"0"*12
        (account / "imported-mods.json").write_text(json.dumps({
            uuid:{"version":"1.2","game_version":"2.45.0","sha256":"a"*64}
        }),"utf-8")
        pack=mod_suite.modpack_manifest(account,[uuid],"Мой набор")
        self.assertEqual(len(pack["mods"]),1)
        self.assertNotIn(str(account),json.dumps(pack))
        self.assertEqual(mod_suite.read_modpack(pack,{uuid}),[uuid])
        self.assertEqual(mod_suite.read_modpack(pack,set()),[])
        with self.assertRaises(ValueError):
            mod_suite.read_modpack({"schema":1,"type":"wtmm-modpack",
                                    "mods":[{"id":"../../"}]},{uuid})


class NetworkModeTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)

    def test_offline_blocks_remote_update_before_network(self):
        with patch.object(offline_mode,"PATH",self.root/"connectivity.json"):
            self.assertTrue(offline_mode.set_offline(True))
            self.assertTrue(offline_mode.is_offline())
            with patch.object(update_checker,"is_offline",return_value=True):
                with patch.object(update_checker,"_api_json") as remote:
                    self.assertIsNone(update_checker.find_update())
                    remote.assert_not_called()
            self.assertFalse(offline_mode.set_offline(False))
            self.assertFalse(offline_mode.is_offline())

    def test_staged_rollout_needs_opt_in_and_honors_pauses(self):
        tag="v1.3.0-beta.16"
        self.assertFalse(release_rollout.eligible(tag,None))
        self.assertTrue(release_rollout.eligible("v1.3.0",None))
        policy={"schema":1,"blocked_tags":[],"staged":{tag:10}}
        self.assertFalse(release_rollout.eligible(tag,policy,{"opt_in":False}))
        self.assertFalse(release_rollout.eligible(tag,{
            **policy,"blocked_tags":[tag]}, {"opt_in":True,"seed":"a"*32}))
        self.assertTrue(release_rollout.eligible(tag,{
            **policy,"staged":{tag:100}}, {}))
        self.assertFalse(release_rollout.eligible(tag,{
            **policy,"staged":{tag:0}}, {}))

    def test_safe_repair_only_creates_missing_library_directories(self):
        with patch.object(diagnostics.profile_paths,"MODS_DIR",self.root/"mods"):
            self.assertEqual(len(diagnostics.repair_safe_folders()),3)
            self.assertEqual(diagnostics.repair_safe_folders(),[])
            (self.root/"mods"/"sights"/"personal.txt").write_text("keep")
            self.assertEqual(diagnostics.repair_safe_folders(),[])
            self.assertEqual((self.root/"mods"/"sights"/"personal.txt").read_text(),"keep")


if __name__=="__main__":
    unittest.main()
