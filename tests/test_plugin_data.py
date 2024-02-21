# -*- encoding: utf-8 -*-
"""Unit tests for the Nendo Core class `PluginData`."""

import unittest

from nendo import Nendo, NendoConfig, NendoPlugin, NendoPluginData

nd = Nendo(
    config=NendoConfig(
        log_level="DEBUG",
        library_path="tests/library",
        library_plugin="default",
        copy_to_library=False,
        max_threads=1,
        plugins=[],
        stream_mode=False,
        stream_chunk_size=3,
    ),
)


class PluginDataTest(unittest.TestCase):
    """Unit test class for testing Nendo plugin data."""

    def test_add_plugin_data(self):
        """Test the adding of plugin data to a `NendoTrack`."""
        nd.library.reset(force=True)
        track = nd.library.add_track(file_path="tests/assets/test.mp3")
        pd = nd.library.add_plugin_data(
            track_id=track.id,
            plugin_name="test_plugin",
            plugin_version="1.0",
            key="test",
            value="value",
        )
        track = nd.library.get_track(track_id=track.id)
        self.assertEqual(len(track.plugin_data), 1)
        self.assertEqual(track.plugin_data[0], pd)

    def test_add_plugin_data_without_version(self):
        """Test the adding of plugin data to a `NendoTrack`."""
        nd.library.reset(force=True)
        my_plugin = NendoPlugin(
            nendo_instance=nd,
            config=nd.config,
            logger=nd.logger,
            plugin_name="test_plugin",
            plugin_version="1.0",
        )
        nd.plugins.add(
            plugin_name="test_plugin",
            version="1.0",
            plugin_instance=my_plugin,
        )
        track = nd.library.add_track(file_path="tests/assets/test.mp3")
        _ = nd.library.add_plugin_data(
            track_id=track.id,
            plugin_name="test_plugin",
            key="test",
            value="value",
        )
        track = nd.library.get_track(track_id=track.id)
        self.assertEqual(len(track.plugin_data), 1)
        self.assertEqual(track.plugin_data[0].plugin_version, "1.0")

    def test_add_plugin_data_without_version_fails(self):
        """Test the adding of plugin data to a `NendoTrack`."""
        nd.library.reset(force=True)
        track = nd.library.add_track(file_path="tests/assets/test.mp3")
        pd = nd.library.add_plugin_data(
            track_id=track.id,
            plugin_name="test_plugin_2",
            key="test",
            value="value",
        )
        track = nd.library.get_track(track_id=track.id)
        self.assertEqual(pd, None)
        self.assertEqual(len(track.plugin_data), 0)

    def test_replace_plugin_data_off(self):
        """Test the adding of plugin data to a `NendoTrack`."""
        nd.library.reset(force=True)
        nd.config.replace_plugin_data = False
        track = nd.library.add_track(file_path="tests/assets/test.mp3")
        nd.library.add_plugin_data(
            track_id=track.id,
            plugin_name="test_plugin",
            plugin_version="1.0",
            key="test",
            value="value",
        )
        nd.library.add_plugin_data(
            track_id=track.id,
            plugin_name="test_plugin",
            plugin_version="1.0",
            key="test",
            value="value2",
        )
        track = nd.library.get_track(track_id=track.id)
        self.assertEqual(len(track.plugin_data), 2)
        nd.library.add_plugin_data(
            track_id=track.id,
            plugin_name="test_plugin",
            plugin_version="1.0",
            key="test",
            value="value",
            replace=True,
        )
        track = nd.library.get_track(track_id=track.id)
        self.assertEqual(len(track.plugin_data), 2)


    def test_replace_plugin_data_on(self):
        """Test the adding of plugin data to a `NendoTrack`."""
        nd.library.reset(force=True)
        nd.config.replace_plugin_data = True
        track = nd.library.add_track(file_path="tests/assets/test.mp3")
        nd.library.add_plugin_data(
            track_id=track.id,
            plugin_name="test_plugin",
            plugin_version="1.0",
            key="test",
            value="value",
        )
        pd_2 = nd.library.add_plugin_data(
            track_id=track.id,
            plugin_name="test_plugin",
            plugin_version="1.0",
            key="test",
            value="value2",
        )
        track = nd.library.get_track(track_id=track.id)
        self.assertEqual(len(track.plugin_data), 1)
        self.assertEqual(track.plugin_data[0].id, pd_2.id)
        nd.library.add_plugin_data(
            track_id=track.id,
            plugin_name="test_plugin",
            plugin_version="1.0",
            key="test",
            value="value2",
            replace=False,
        )
        track = nd.library.get_track(track_id=track.id)
        self.assertEqual(len(track.plugin_data), 2)
        nd.config.replace_plugin_data = False

    def test_get_plugin_data(self):
        """Test the getting of plugin data from a `NendoTrack`."""
        nd.library.reset(force=True)
        track = nd.library.add_track(file_path="tests/assets/test.mp3")
        _ = nd.library.add_plugin_data(
            track_id=track.id,
            plugin_name="test_plugin",
            plugin_version="1.0",
            key="test",
            value="value",
        )
        _ = nd.library.add_plugin_data(
            track_id=track.id,
            plugin_name="test_plugin",
            plugin_version="1.0",
            key="test2",
            value="value2",
        )
        track = nd.library.get_track(track_id=track.id)
        plugin_data = track.get_plugin_data(plugin_name="test_plugin")
        self.assertEqual(type(plugin_data), list)
        self.assertEqual(len(plugin_data), 2)
        self.assertEqual(type(plugin_data[0]), NendoPluginData)
        plugin_data_2 = track.get_plugin_data(plugin_name="test_plugin", key="test2")
        self.assertEqual(type(plugin_data_2), list)
        self.assertEqual(plugin_data_2[0].value, "value2")

    def test_get_plugin_value(self):
        """Test the getting of a single plugin value from `NendoTrack`."""
        nd.library.reset(force=True)
        track = nd.library.add_track(file_path="tests/assets/test.mp3")
        _ = nd.library.add_plugin_data(
            track_id=track.id,
            plugin_name="test_plugin",
            plugin_version="1.0",
            key="test",
            value="value",
        )
        track = nd.library.get_track(track_id=track.id)
        plugin_value = track.get_plugin_value("test")
        self.assertEqual(type(plugin_value), str)
        self.assertEqual(plugin_value, "value")

    def test_filter_random_track(self):
        """Test the retrieval of a random `NendoTrack` from the library."""
        nd.library.reset(force=True)
        track = nd.library.add_track(file_path="tests/assets/test.mp3")
        pd = nd.library.add_plugin_data(
            track_id=track.id,
            plugin_name="test_plugin",
            plugin_version="1.0",
            key="test",
            value="value",
        )
        example_data = nd.library.filter_tracks(
            filters={"test": "value"},
            order_by="random",
            plugin_names=["test_plugin"],
        )[0].get_plugin_data(plugin_name="test_plugin")
        self.assertEqual(type(example_data), list)
        self.assertEqual(example_data[0].value, pd.value)

    def test_filter_by_plugin_data(self):
        """Test filtering by plugin data and track file name."""
        nd.library.reset(force=True)
        track = nd.library.add_track(file_path="tests/assets/test.mp3")
        pd = nd.library.add_plugin_data(
            track_id=track.id,
            plugin_name="test_plugin",
            plugin_version="1.0",
            key="test",
            value="value",
        )
        example_data = nd.library.filter_tracks(
            filters={"test": "value"},
            plugin_names=["test_plugin"],
        )[0].get_plugin_data(plugin_name="test_plugin")
        self.assertEqual(type(example_data), list)
        self.assertEqual(example_data[0].value, pd.value)

    def test_filter_tracks_by_plugin_data(self):
        """Test the filtering of `NendoTrack`s by plugin data."""
        nd.library.reset(force=True)
        track = nd.library.add_track(file_path="tests/assets/test.mp3")
        pd = nd.library.add_plugin_data(
            track_id=track.id,
            plugin_name="test_plugin",
            plugin_version="1.0",
            key="foo",
            value="bar",
        )
        track = nd.library.get_track(track_id=track.id)
        example_data = nd.library.filter_tracks(
            filters={"foo": "bar"},
            plugin_names=["test_plugin"],
        )[0].get_plugin_data(plugin_name="test_plugin")
        self.assertEqual(type(example_data), list)
        self.assertEqual(example_data[0].value, track.plugin_data[0].value)
        example_data = nd.library.filter_tracks(
            filters={"foo": ["bar", "baz"]},
            plugin_names=["test_plugin"],
        )[0].get_plugin_data(plugin_name="test_plugin")
        self.assertEqual(type(example_data), list)
        self.assertEqual(example_data[0].value, pd.value)
        example_data = nd.library.filter_tracks(
            filters={"foo": ["bat", "baz"]},
            plugin_names=["test_plugin"],
        )
        self.assertEqual(len(example_data), 0)
        pd2 = nd.library.add_plugin_data(
            track_id=track.id,
            plugin_name="test_plugin",
            plugin_version="1.0",
            key="number",
            value="15.10289371",
        )
        track = nd.library.get_track(track_id=track.id)
        example_data = nd.library.filter_tracks(
            filters={"number": (10.0, 20.0)},
            plugin_names=["test_plugin"],
        )[0].get_plugin_data(plugin_name="test_plugin", key="number")
        self.assertEqual(type(example_data), list)
        self.assertEqual(example_data[0].value, pd2.value)
        example_data = nd.library.filter_tracks(
            filters={"number": (10, 20)},
            plugin_names=["test_plugin"],
        )[0].get_plugin_data(plugin_name="test_plugin", key="number")
        self.assertEqual(type(example_data), list)
        self.assertEqual(example_data[0].value, pd2.value)
        example_data = nd.library.filter_tracks(
            filters={"number": (20.0, 30.0)},
            plugin_names=["test_plugin"],
        )
        self.assertEqual(len(example_data), 0)

    def test_filter_tracks_by_multiple_plugin_keys(self):
        """Test the filtering of `NendoTrack`s by multiple plugin keys."""
        nd.library.reset(force=True)
        track = nd.library.add_track(file_path="tests/assets/test.mp3")
        nd.library.add_plugin_data(
            track_id=track.id,
            plugin_name="test_plugin",
            plugin_version="1.0",
            key="foo1",
            value="bar1",
        )
        nd.library.add_plugin_data(
            track_id=track.id,
            plugin_name="test_plugin",
            plugin_version="1.0",
            key="foo2",
            value="bar2",
        )
        nd.library.add_plugin_data(
            track_id=track.id,
            plugin_name="test_plugin",
            plugin_version="1.0",
            key="number",
            value="15.10289371",
        )
        example_data = nd.library.filter_tracks(
            filters={"foo1": ["bar1", "baz1"], "foo2": "bar2", "number": (12.0, 18.0)},
            plugin_names=["test_plugin"],
        )
        self.assertEqual(len(example_data), 1)
        example_data = nd.library.filter_tracks(
            filters={"foo1": ["bar1", "baz1"], "foo2": "bar3", "number": (12.0, 18.0)},
            plugin_names=["test_plugin"],
        )
        self.assertEqual(len(example_data), 0)
        example_data = nd.library.filter_tracks(
            filters={"foo1": ["bar1", "baz1"], "foo2": "bar2", "number": (20.0, 21.0)},
            plugin_names=["test_plugin"],
        )
        self.assertEqual(len(example_data), 0)
        example_data = nd.library.filter_tracks(
            filters={"foo1": ["bat1", "baz1"], "foo2": "bar2", "number": (12.0, 18.0)},
            plugin_names=["test_plugin"],
        )
        self.assertEqual(len(example_data), 0)


if __name__ == "__main__":
    unittest.main()
