"""Unit tests for the Nendo plugin system."""
import unittest
from unittest.mock import Mock, patch

import numpy as np

from nendo import (
    DuckDBLibrary,
    Nendo,
    NendoAnalysisPlugin,
    NendoCollection,
    NendoConfig,
    NendoEffectPlugin,
    NendoEmbeddingPlugin,
    NendoGeneratePlugin,
    NendoTrack,
)
with patch.object(DuckDBLibrary, 'add_embedding', Mock(), create=True) as mock_method:
    nd = Nendo(
        config=NendoConfig(
            log_level="DEBUG",
            library_plugin="default",
            library_path="tests/library",
            copy_to_library=False,
        ),
    )

def init_plugin(clazz):
    """Helper function to initialize a plugin for tests."""
    return clazz(
        nendo_instance=nd,
        config=NendoConfig(),
        logger=nd.logger,
        plugin_name="test_plugin",
        plugin_version="0.1",
    )


class ExampleAnalysisPlugin(NendoAnalysisPlugin):
    """Example plugin for testing the NendoAnalysisPlugin class."""

    @NendoAnalysisPlugin.run_track
    def track_function(self, track):
        """Example track function."""

    @NendoAnalysisPlugin.run_collection
    def collection_function(self, collection):
        """Example collection function."""


class ExampleEffectPlugin(NendoEffectPlugin):
    """Example plugin for testing the NendoEffectPlugin class."""

    @NendoEffectPlugin.run_track
    def track_function(self, track=None):
        """Example track function."""
        return track

    @NendoEffectPlugin.run_collection
    def collection_function(self, collection=None):
        """Example collection function."""
        return collection

    @NendoEffectPlugin.run_signal
    def signal_function(self, signal=None, sr=None):
        """Example signal function."""
        return signal, sr


class ExampleGeneratePlugin(NendoGeneratePlugin):
    """Example plugin for testing the NendoGeneratePlugin class."""

    @NendoGeneratePlugin.run_track
    def track_function(self, track=None):
        """Example track function."""
        if track is None:
            track = nd.library.add_track(file_path="tests/assets/test.wav")
        return track

    @NendoGeneratePlugin.run_track
    def track_list_function(self, track=None):
        """Example track list function."""
        if track is None:
            track = nd.library.add_track(file_path="tests/assets/test.wav")
        track_2 = nd.library.add_track(file_path="tests/assets/test.mp3")
        return [track, track_2]

    @NendoGeneratePlugin.run_collection
    def collection_function(self, collection=None):
        """Example collection function."""
        if collection is None:
            track = nd.library.add_track(file_path="tests/assets/test.wav")
            collection = nd.library.add_collection(
                name="test_collection",
                track_ids=[track.id],
            )
        return collection

    @NendoGeneratePlugin.run_signal
    def signal_function(self, signal=None, sr=None):
        """Example signal function."""
        if signal is None:
            signal, sr = np.zeros([2, 23000]), 44100
        return signal, sr

class ExampleEmbeddingPlugin(NendoEmbeddingPlugin):
    """Example plugin for testing the NendoEmbeddingPlugin class."""

    # @NendoEmbeddingPlugin.run_text
    # def text_function(self, text=None):
    #     """Example text function."""
    #     return (text or "test"), np.zeros(5)

    # @NendoEmbeddingPlugin.run_signal_and_text
    # def signal_function(self, signal=None, sr=None, text=None):
    #     """Example signal and text function."""
    #     return (text or "test"), np.zeros(5)

    @NendoEmbeddingPlugin.run_track
    def track_function(self, track=None):
        """Example track function."""
        return "test", np.zeros(5)

    # @NendoEmbeddingPlugin.run_collection
    # def collection_function(self, collection=None):
    #     """Example collection function."""
    #     return "test", np.zeros(5)


# class NendoAnalysisPluginTest(unittest.TestCase):
#     """Unit test class for testing the NendoAnalysisPlugin class."""

#     def test_run_track_decorator_with_track(self):
#         """Test the `NendoAnalysisPlugin.run_track` decorator with a `NendoTrack`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleAnalysisPlugin)
#         track = nd.library.add_track(file_path="tests/assets/test.wav")

#         result = plug.track_function(track=track)
#         self.assertEqual(type(result), NendoTrack)
#         self.assertEqual(result.id, track.id)

#     def test_run_track_decorator_with_collection(self):
#         """Test the `NendoAnalysisPlugin.run_track` decorator with a `NendoCollection`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleAnalysisPlugin)
#         track = nd.library.add_track(file_path="tests/assets/test.wav")
#         coll = nd.library.add_collection(name="test_collection", track_ids=[track.id])

#         result = plug.track_function(collection=coll)
#         self.assertEqual(type(result), NendoCollection)
#         self.assertEqual(len(result), 1)
#         self.assertEqual(result[0].id, track.id)

#     def test_run_collection_decorator_with_track(self):
#         """Test the `NendoAnalysisPlugin.run_collection` decorator with a `NendoTrack`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleAnalysisPlugin)
#         track = nd.library.add_track(file_path="tests/assets/test.wav")

#         result = plug.collection_function(track=track)
#         self.assertEqual(type(result), NendoTrack)
#         self.assertEqual(result.id, track.id)

#     def test_run_collection_decorator_with_collection(self):
#         """Test the `NendoAnalysisPlugin.run_collection` decorator with a `NendoCollection`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleAnalysisPlugin)
#         track = nd.library.add_track(file_path="tests/assets/test.wav")
#         coll = nd.library.add_collection(name="test_collection", track_ids=[track.id])

#         result = plug.collection_function(collection=coll)
#         self.assertEqual(type(result), NendoCollection)
#         self.assertEqual(len(result), 1)
#         self.assertEqual(result[0].id, track.id)


# class NendoGeneratePluginTest(unittest.TestCase):
#     """Unit test class for testing the NendoGeneratePlugin class."""

#     def test_run_track_decorator_with_track(self):
#         """Test the `NendoGeneratePlugin.run_track` decorator with a `NendoTrack`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleGeneratePlugin)
#         track = nd.library.add_track(file_path="tests/assets/test.wav")

#         result = plug.track_function(track=track)
#         self.assertEqual(type(result), NendoTrack)
#         self.assertEqual(result.id, track.id)

#     def test_run_track_decorator_with_none(self):
#         """Test the `NendoGeneratePlugin.run_track` decorator with a `None`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleGeneratePlugin)

#         result = plug.track_function()
#         self.assertEqual(type(result), NendoTrack)

#     def test_run_track_decorator_with_collection(self):
#         """Test the `NendoGeneratePlugin.run_track` decorator with a `NendoCollection`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleGeneratePlugin)
#         track = nd.library.add_track(file_path="tests/assets/test.wav")
#         coll = nd.library.add_collection(name="test_collection", track_ids=[track.id])

#         result = plug.track_function(collection=coll)
#         self.assertEqual(type(result), NendoCollection)
#         self.assertEqual(len(result), 1)

#     def test_run_track_list_decorator_with_track(self):
#         """Test the `NendoGeneratePlugin.run_track_list` decorator with a `NendoTrack`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleGeneratePlugin)
#         track = nd.library.add_track(file_path="tests/assets/test.wav")

#         result = plug.track_list_function(track=track)
#         self.assertEqual(type(result), NendoCollection)
#         self.assertEqual(len(result), 2)

#     def test_run_track_list_decorator_with_collection(self):
#         """Test the `NendoGeneratePlugin.run_track_list` decorator with a `NendoCollection`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleGeneratePlugin)
#         track = nd.library.add_track(file_path="tests/assets/test.wav")
#         coll = nd.library.add_collection(name="test_collection", track_ids=[track.id])

#         result = plug.track_list_function(collection=coll)
#         self.assertEqual(type(result), NendoCollection)
#         self.assertEqual(len(result), 2)

#     def test_run_track_list_decorator_with_none(self):
#         """Test the `NendoGeneratePlugin.run_track_list` decorator with a `None`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleGeneratePlugin)

#         result = plug.track_list_function()
#         self.assertEqual(type(result), NendoCollection)
#         self.assertEqual(len(result), 2)

#     def test_run_collection_decorator_with_track(self):
#         """Test the `NendoGeneratePlugin.run_collection` decorator with a `NendoTrack`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleGeneratePlugin)
#         track = nd.library.add_track(file_path="tests/assets/test.wav")

#         result = plug.collection_function(track=track)
#         self.assertEqual(type(result), NendoCollection)
#         self.assertEqual(len(result), 1)

#     def test_run_collection_decorator_with_collection(self):
#         """Test the `NendoGeneratePlugin.run_collection` decorator with a `NendoCollection`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleGeneratePlugin)
#         track = nd.library.add_track(file_path="tests/assets/test.wav")
#         coll = nd.library.add_collection(name="test_collection", track_ids=[track.id])

#         result = plug.collection_function(collection=coll)
#         self.assertEqual(type(result), NendoCollection)
#         self.assertEqual(len(result), 1)

#     def test_run_collection_decorator_with_none(self):
#         """Test the `NendoGeneratePlugin.run_collection` decorator with a `None`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleGeneratePlugin)

#         result = plug.collection_function()
#         self.assertEqual(type(result), NendoCollection)
#         self.assertEqual(len(result), 1)

#     def test_run_signal_decorator_with_track(self):
#         """Test the `NendoGeneratePlugin.run_signal` decorator with a `NendoTrack`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleGeneratePlugin)
#         track = nd.library.add_track(file_path="tests/assets/test.wav")

#         result = plug.signal_function(track=track)
#         self.assertEqual(type(result), NendoTrack)

#     def test_run_signal_decorator_with_collection(self):
#         """Test the `NendoGeneratePlugin.run_signal` decorator with a `NendoCollection`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleGeneratePlugin)
#         track = nd.library.add_track(file_path="tests/assets/test.wav")
#         coll = nd.library.add_collection(name="test_collection", track_ids=[track.id])

#         result = plug.signal_function(collection=coll)
#         self.assertEqual(type(result), NendoCollection)
#         self.assertEqual(len(result), 1)

#     def test_run_signal_decorator_with_none(self):
#         """Test the `NendoGeneratePlugin.run_signal` decorator with a `None`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleGeneratePlugin)

#         result = plug.signal_function()
#         self.assertEqual(type(result), NendoTrack)


# class NendoEffectPluginTest(unittest.TestCase):
#     """Unit test class for testing the NendoEffectPlugin class."""

#     def test_run_track_decorator_with_track(self):
#         """Test the `NendoEffectPlugin.run_track` decorator with a `NendoTrack`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleEffectPlugin)
#         track = nd.library.add_track(file_path="tests/assets/test.wav")

#         result = plug.track_function(track=track)
#         self.assertEqual(type(result), NendoTrack)
#         self.assertEqual(result.id, track.id)

#     def test_run_track_decorator_with_collection(self):
#         """Test the `NendoEffectPlugin.run_track` decorator with a `NendoCollection`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleEffectPlugin)
#         track = nd.library.add_track(file_path="tests/assets/test.wav")
#         coll = nd.library.add_collection(name="test_collection", track_ids=[track.id])

#         result = plug.track_function(collection=coll)
#         self.assertEqual(type(result), NendoCollection)
#         self.assertEqual(len(result), 1)

#     def test_run_collection_decorator_with_track(self):
#         """Test the `NendoEffectPlugin.run_collection` decorator with a `NendoTrack`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleEffectPlugin)
#         track = nd.library.add_track(file_path="tests/assets/test.wav")

#         result = plug.collection_function(track=track)
#         self.assertEqual(type(result), NendoCollection)
#         self.assertEqual(len(result), 1)

#     def test_run_collection_decorator_with_collection(self):
#         """Test the `NendoEffectPlugin.run_collection` decorator with a `NendoCollection`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleEffectPlugin)
#         track = nd.library.add_track(file_path="tests/assets/test.wav")
#         coll = nd.library.add_collection(name="test_collection", track_ids=[track.id])

#         result = plug.collection_function(collection=coll)
#         self.assertEqual(type(result), NendoCollection)
#         self.assertEqual(len(result), 1)

#     def test_run_signal_decorator_with_track(self):
#         """Test the `NendoEffectPlugin.run_signal` decorator with a `NendoTrack`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleEffectPlugin)
#         track = nd.library.add_track(file_path="tests/assets/test.wav")

#         result = plug.signal_function(track=track)
#         self.assertEqual(type(result), NendoTrack)

#     def test_run_signal_decorator_with_collection(self):
#         """Test the `NendoEffectPlugin.run_signal` decorator with a `NendoCollection`."""
#         nd.library.reset(force=True)
#         plug = init_plugin(ExampleEffectPlugin)
#         track = nd.library.add_track(file_path="tests/assets/test.wav")
#         coll = nd.library.add_collection(name="test_collection", track_ids=[track.id])

#         result = plug.signal_function(collection=coll)
#         self.assertEqual(type(result), NendoCollection)
#         self.assertEqual(len(result), 1)

class NendoEmbeddingPluginTest(unittest.TestCase):
    """Unit test class for testing the NendoEffectPlugin class."""

    def test_run_track_decorator_with_track(self):
        """Test the `NendoEmbeddingPlugin.run_track` decorator with a `NendoTrack`."""
        nd.library.reset(force=True)
        plug = init_plugin(ExampleEmbeddingPlugin)
        track = nd.library.add_track(file_path="tests/assets/test.wav")

        result = plug.track_function(track=track)
        self.assertEqual(type(result), NendoTrack)
        self.assertEqual(result.id, track.id)

    # def test_run_track_decorator_with_collection(self):
    #     """Test the `NendoEmbeddingPlugin.run_track` decorator with a `NendoCollection`."""
    #     nd.library.reset(force=True)
    #     plug = init_plugin(ExampleEmbeddingPlugin)
    #     track = nd.library.add_track(file_path="tests/assets/test.wav")
    #     coll = nd.library.add_collection(name="test_collection", track_ids=[track.id])

    #     result = plug.track_function(collection=coll)
    #     self.assertEqual(type(result), NendoCollection)
    #     self.assertEqual(len(result), 1)

    # def test_run_collection_decorator_with_track(self):
    #     """Test the `NendoEmbeddingPlugin.run_collection` decorator with a `NendoTrack`."""
    #     nd.library.reset(force=True)
    #     plug = init_plugin(ExampleEmbeddingPlugin)
    #     track = nd.library.add_track(file_path="tests/assets/test.wav")

    #     result = plug.collection_function(track=track)
    #     self.assertEqual(type(result), NendoCollection)
    #     self.assertEqual(len(result), 1)

    # def test_run_collection_decorator_with_collection(self):
    #     """Test the `NendoEmbeddingPlugin.run_collection` decorator with a `NendoCollection`."""
    #     nd.library.reset(force=True)
    #     plug = init_plugin(ExampleEmbeddingPlugin)
    #     track = nd.library.add_track(file_path="tests/assets/test.wav")
    #     coll = nd.library.add_collection(name="test_collection", track_ids=[track.id])

    #     result = plug.collection_function(collection=coll)
    #     self.assertEqual(type(result), NendoCollection)
    #     self.assertEqual(len(result), 1)

    # def test_run_signal_decorator_with_track(self):
    #     """Test the `NendoEmbeddingPlugin.run_signal` decorator with a `NendoTrack`."""
    #     nd.library.reset(force=True)
    #     plug = init_plugin(ExampleEmbeddingPlugin)
    #     track = nd.library.add_track(file_path="tests/assets/test.wav")

    #     result = plug.signal_function(track=track)
    #     self.assertEqual(type(result), NendoTrack)

    # def test_run_signal_decorator_with_collection(self):
    #     """Test the `NendoEmbeddingPlugin.run_signal` decorator with a `NendoCollection`."""
    #     nd.library.reset(force=True)
    #     plug = init_plugin(ExampleEmbeddingPlugin)
    #     track = nd.library.add_track(file_path="tests/assets/test.wav")
    #     coll = nd.library.add_collection(name="test_collection", track_ids=[track.id])

    #     result = plug.signal_function(collection=coll)
    #     self.assertEqual(type(result), NendoCollection)
    #     self.assertEqual(len(result), 1)
