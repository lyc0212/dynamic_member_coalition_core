"""核对冻结输入。自主前缀单独执行一次，回归测试不重复运行它。"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name):
    return json.loads((ROOT / 'configs' / name).read_text(encoding='utf-8'))

class SwitchInputs(unittest.TestCase):
    def test_only_registered_world_parameters_change(self):
        expected = load('a2_two_target_staggered_min.json')
        expected['targets'][0]['service_duration'] = 2.25
        expected['targets'][1].update(weight=1.5, deadline=5.0)
        self.assertEqual(load('a2_switch_two_target_v1.json'), expected)

    def test_only_registered_announcement_parameters_change(self):
        expected = load('a2_public_announcements.json')
        expected['announcements'][0]['service_duration'] = 2.25
        expected['announcements'][1].update(weight=1.5, deadline=5.0)
        self.assertEqual(load('a2_switch_public_announcements_v1.json'), expected)

    def test_public_metadata_matches_world(self):
        world = load('a2_switch_two_target_v1.json')
        announcements = load('a2_switch_public_announcements_v1.json')['announcements']
        self.assertEqual(len(world['targets']), len(announcements))
        fields = ('id', 'birth', 'weight', 'deadline', 'service_duration', 'required_robots')
        for target, announcement in zip(world['targets'], announcements):
            self.assertEqual({k: target[k] for k in fields}, {k: announcement[k] for k in fields})
            self.assertEqual(announcement['announcement_tick'], round(target['birth'] / world['config']['step_dt']))

if __name__ == '__main__':
    unittest.main()
