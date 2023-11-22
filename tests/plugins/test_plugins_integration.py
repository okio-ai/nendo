# -*- encoding: utf-8 -*-
"""Unit tests for testing the integration of Nendo plugins."""

import unittest

from nendo import Nendo, NendoConfig

# load all plugins and see if that works
nd = Nendo(
    config=NendoConfig(
        library_path="tests/library",
        log_level="DEBUG",
        copy_to_library=False,
        plugins=[
            "nendo_plugin_stemify_demucs",
            "nendo_plugin_loopify",
            "nendo_plugin_classify_core",
            "nendo_plugin_quantize_core",
            "nendo_plugin_vampnet",
            "nendo_plugin_musicgen",
            "nendo_plugin_remixer",
        ],
    ),
)


@unittest.skip("skip temporarily until we decide on which plugins we want for release")
class PluginIntegrationSmokeTest(unittest.TestCase):
    """Unit test class for testing the integration of nendo plugins."""

    def test_run_all_plugins_with_empty_collection(self):
        """Test the running of multiple plugins on an empty collection."""
        nd.library.reset(force=True)
        collection = nd.library.add_collection(name="empty_test_collection")

        collection = nd.plugins.classify_core(collection=collection)
        collection = nd.plugins.quantize_core(collection=collection)
        collection = nd.plugins.stemify_demucs(collection=collection)
        collection = nd.plugins.loopify(collection=collection)
        collection = nd.plugins.vampnet(collection=collection)
        collection = nd.plugins.musicgen(collection=collection)
        collection = nd.plugins.remixer(collection=collection)
        self.assertIsNotNone(collection)

    def test_run_all_plugins_with_single_track_collection(self):
        """Test the running of all plugins on a collection with a single track."""
        nd.library.reset(force=True)
        track = nd.library.add_track(file_path="./assets/test.wav")
        collection = nd.library.add_collection(
            name="single_track_collection",
            track_ids=[track.id],
        )

        # collection = nd.plugins.quantize_core(collection=collection)
        classified_collection = nd.plugins.classify_core(collection=collection)
        stemified_collection = nd.plugins.stemify_demucs(
            collection=classified_collection,
        )
        loopified_collection = nd.plugins.loopify(collection=classified_collection)
        vamped_collection = nd.plugins.vampnet(collection=classified_collection)
        musicgen_collection = nd.plugins.musicgen(collection=classified_collection)

        self.assertIsNotNone(classified_collection)
        self.assertIsNotNone(stemified_collection)
        self.assertIsNotNone(loopified_collection)
        self.assertIsNotNone(vamped_collection)
        self.assertIsNotNone(musicgen_collection)


if __name__ == "__main__":
    unittest.main()
