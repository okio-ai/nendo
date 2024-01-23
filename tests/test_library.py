# -*- encoding: utf-8 -*-
"""Tests for the Nendo Core default library implementation."""

import os
import unittest
from types import GeneratorType

from nendo import Nendo, NendoCollection, NendoConfig, NendoTrack

nd = Nendo(
    config=NendoConfig(
        log_level="DEBUG",
        library_plugin="default",
        library_path="tests/library",
        copy_to_library=False,
        max_threads=1,
        plugins=[],
        stream_mode=False,
        stream_chunk_size=3,
    ),
)


class DefaultLibraryTests(unittest.TestCase):
    """Unit test class for testing the default (DuckDB) library."""

    # def test_create_track(self):
    #     nd.library.reset(force=True)
    #     new_track = nd.library.create_object(
    #         track_type="track",
    #         meta={
    #             "test": "ok",
    #         },
    #     )
    #     self.assertTrue(isinstance(new_track, NendoTrack))
    #     retrieved_track = nd.library.get_track(new_track.id)
    #     self.assertEqual(retrieved_track.track_type, "track")
    #     self.assertTrue(retrieved_track.has_meta("test"))
    #     self.assertEqual(retrieved_track.get_meta("test"), "ok")

    # def test_len_library(self):
    #     """Test `len(nd.library)`."""
    #     nd.library.reset(force=True)
    #     nd.library.add_track(file_path="tests/assets/test.mp3")
    #     nd.library.add_track(file_path="tests/assets/test.wav")
    #     self.assertEqual(len(nd.library), 2)

    # def test_iter_library(self):
    #     """Test iterating over the library items."""
    #     nd.library.reset(force=True)
    #     nd.library.add_track(file_path="tests/assets/test.mp3")
    #     nd.library.add_track(file_path="tests/assets/test.wav")
    #     for track in nd.library:
    #         self.assertTrue(isinstance(track, NendoTrack))

    # def test_add_file_to_library(self):
    #     """Test adding a file to the library using the `add_track()` method."""
    #     nd.library.reset(force=True)
    #     inserted_track = nd.library.add_track(file_path="tests/assets/test.wav")
    #     queried_track = nd.library.get_track(inserted_track.id)
    #     self.assertIsNotNone(queried_track)

    #     queried_tracks = nd.library.get_tracks()
    #     self.assertEqual(len(queried_tracks), 1)

    # def test_add_related_to_library(self):
    #     """Test adding a related track to the library."""
    #     nd.library.reset(force=True)
    #     inserted_track1 = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     nd.library.add_related_track(
    #         file_path="tests/assets/test.wav",
    #         related_track_id=inserted_track1.id,
    #         relationship_type="stem",
    #         meta={"test": "value"},
    #     )
    #     inserted_track1.refresh()
    #     self.assertTrue(inserted_track1.has_relationship("stem"))
    #     self.assertEqual(len(inserted_track1.related_tracks), 1)
    #     self.assertEqual(inserted_track1.related_tracks[0].meta, {"test": "value"})

    # def test_add_track_relationship_with_track_ids_library(self):
    #     """Test the `add_track_relationship()` method."""
    #     nd.library.reset(force=True)
    #     inserted_track1 = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     inserted_track2 = nd.library.add_track(file_path="tests/assets/test.wav")

    #     nd.library.add_track_relationship(
    #         track_one_id=inserted_track1.id,
    #         track_two_id=inserted_track2.id,
    #         relationship_type="stem",
    #         meta={"test": "value"},
    #     )

    #     related_tracks = nd.library.get_related_tracks(inserted_track2.id)
    #     self.assertEqual(len(related_tracks), 1)

    # def test_get_tracks_returns_tracks(self):
    #     """Test the `nd.library.get_tracks()` method."""
    #     nd.library.reset(force=True)
    #     nd.library.add_track(file_path="tests/assets/test.mp3")
    #     nd.library.add_track(file_path="tests/assets/test.wav")
    #     all_tracks = nd.library.get_tracks()
    #     self.assertEqual(len(all_tracks), 2)

    # def test_get_tracks_order_by_returns_asc_ordered_tracks(self):
    #     """Test the ordering of tracks returned by the `get_tracks()` method."""
    #     nd.library.reset(force=True)
    #     nd.library.add_track(file_path="tests/assets/test.mp3")
    #     nd.library.add_track(file_path="tests/assets/test.wav")
    #     all_tracks = nd.library.get_tracks(order_by="created_at", order="asc")
    #     self.assertEqual(len(all_tracks), 2)
    #     self.assertTrue(all_tracks[1].created_at > all_tracks[0].created_at)

    # def test_get_tracks_order_by_returns_desc_ordered_tracks(self):
    #     """Test the ordering of tracks returned by the `get_tracks()` method."""
    #     nd.library.reset(force=True)
    #     nd.library.add_track(file_path="tests/assets/test.mp3")
    #     nd.library.add_track(file_path="tests/assets/test.wav")
    #     all_tracks = nd.library.get_tracks(order_by="created_at", order="desc")
    #     self.assertEqual(len(all_tracks), 2)
    #     self.assertTrue(all_tracks[1].created_at < all_tracks[0].created_at)

    # def test_get_tracks_returns_limited_offset_tracks(self):
    #     """Test the limit/offset functionality of `nd.library.get_tracks()`."""
    #     nd.library.reset(force=True)
    #     nd.library.add_track(file_path="tests/assets/test.mp3")
    #     nd.library.add_track(file_path="tests/assets/test.wav")
    #     limit_tracks = nd.library.get_tracks(limit=1)
    #     offset_tracks = nd.library.get_tracks(limit=1, offset=1)

    #     self.assertEqual(len(limit_tracks), 1)
    #     self.assertEqual(len(offset_tracks), 1)
    #     self.assertNotEqual(limit_tracks, offset_tracks)

    # def test_get_tracks_returns_limit_tracks(self):
    #     """Test the limit argument of `nd.library.get_tracks()`."""
    #     nd.library.reset(force=True)
    #     nd.library.add_track(file_path="tests/assets/test.mp3")
    #     nd.library.add_track(file_path="tests/assets/test.wav")
    #     all_tracks = nd.library.get_tracks(limit=2)
    #     self.assertEqual(len(all_tracks), 2)

    def test_filter_tracks_returns_filtered_tracks(self):
        """Test filtering of tracks."""
        nd.library.reset(force=True)
        inserted_track1 = nd.library.add_track(
            file_path="tests/assets/test.mp3",
            meta = {"test_meta_key": "test_meta_value"},
        )
        nd.library.add_track(file_path="tests/assets/test.wav")
        nd.library.add_plugin_data(
            track_id=inserted_track1.id,
            plugin_name="test_plugin",
            plugin_version="1.0",
            key="test",
            value="value",
        )
        # with explicit plugin_names
        retrieved_tracks = nd.library.filter_tracks(
            filters={"test": "value"},
            plugin_names=["test_plugin"],
        )
        self.assertEqual(len(retrieved_tracks), 1)
        self.assertEqual(retrieved_tracks[0].id, inserted_track1.id)
        # without plugin_names should just return all
        retrieved_tracks = nd.library.filter_tracks(
            filters={"test": "value"},
        )
        self.assertEqual(len(retrieved_tracks), 1)
        self.assertEqual(retrieved_tracks[0].id, inserted_track1.id)
        # with empty plugin_names list should also return all
        retrieved_tracks = nd.library.filter_tracks(
            filters={"test": "value"},
            plugin_names=[],
        )
        self.assertEqual(len(retrieved_tracks), 1)
        self.assertEqual(retrieved_tracks[0].id, inserted_track1.id)

        example_data = nd.library.filter_tracks(
            search_meta=["test_meta_value"],
        )
        self.assertEqual(len(example_data), 1)
        self.assertEqual(example_data[0].id, inserted_track1.id)
        example_data = nd.library.filter_tracks(
            search_meta=["assets", "test."],
        )
        self.assertEqual(len(example_data), 2)
        example_data = nd.library.filter_tracks(
            search_meta=["wrong_meta_value"],
        )
        self.assertEqual(len(example_data), 0)

    # def test_filter_by_track_type(self):
    #     """Test filtering by track type."""
    #     nd.library.reset(force=True)
    #     test_track_1 = nd.library.add_track(
    #         file_path="tests/assets/test.mp3",
    #         track_type="stem",
    #     )
    #     nd.library.add_track(file_path="tests/assets/test.wav", track_type="track")
    #     result = nd.library.filter_tracks(track_type="stem")
    #     self.assertEqual(len(result), 1)
    #     self.assertEqual(result[0].id, test_track_1.id)
    #     result = nd.library.filter_tracks(track_type=["stem", "track"])
    #     self.assertEqual(len(result), 2)

    # def test_get_tracks_filtered_by_collection(self):
    #     """Test filtering of tracks by collection."""
    #     nd.library.reset(force=True)
    #     inserted_track1 = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     nd.library.add_track(file_path="tests/assets/test.wav")

    #     collection = nd.library.add_collection(
    #         name="test_collection_filter",
    #         track_ids=[inserted_track1.id],
    #     )

    #     all_tracks = nd.library.filter_tracks(collection_id=collection.id)
    #     self.assertEqual(len(all_tracks), 1)

    # def test_find_in_library(self):
    #     """Test the function for finding tracks in the library."""
    #     nd.library.reset(force=True)
    #     inserted_track1 = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     inserted_track2 = nd.library.add_track(file_path="tests/assets/test.wav")
    #     result = nd.library.find_tracks(value="Test Artist")
    #     self.assertEqual(len(result), 2)
    #     self.assertEqual(result[0].id, inserted_track1.id)
    #     result = nd.library.find_tracks(value="test.wav")
    #     self.assertEqual(len(result), 1)
    #     self.assertEqual(result[0].id, inserted_track2.id)

    # def test_find_related_tracks_in_library(self):
    #     """Test the finding of related tracks in the library."""
    #     nd.library.reset(force=True)
    #     nd.config.skip_duplicate = False
    #     inserted_track1 = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     inserted_track2 = nd.library.add_related_track(
    #         file_path="tests/assets/test.wav",
    #         related_track_id=inserted_track1.id,
    #         relationship_type="stem",
    #         meta={"test": "value"},
    #     )
    #     nd.library.add_related_track(
    #         file_path="tests/assets/test.mp3",
    #         related_track_id=inserted_track1.id,
    #         relationship_type="stem",
    #         meta={"test": "value"},
    #     )

    #     related_tracks = nd.library.get_related_tracks(inserted_track1.id)
    #     self.assertEqual(len(related_tracks), 2)
    #     related_tracks_2_from = nd.library.get_related_tracks(
    #         inserted_track2.id,
    #         direction="from",
    #     )
    #     self.assertEqual(len(related_tracks_2_from), 1)
    #     nd.config.skip_duplicate = True

    # def test_add_file_without_conversion(self):
    #     """Test adding a file to the library without conversion."""
    #     nd.config.copy_to_library = True
    #     nd.config.auto_convert = False
    #     nd.library.reset(force=True)
    #     inserted_track = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     self.assertEqual(os.path.splitext(inserted_track.resource.src)[1], ".mp3")
    #     nd.config.auto_convert = True
    #     nd.config.copy_to_library = False

    # def test_add_file_skip_duplicate(self):
    #     """Test the `skip_duplicate` config variable."""
    #     nd.config.skip_duplicate = False
    #     nd.library.reset(force=True)
    #     inserted_track_1 = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     inserted_track_2 = nd.library.add_track(
    #         file_path="tests/assets/test.mp3",
    #         skip_duplicate=True,
    #     )
    #     self.assertEqual(len(nd.library), 1)
    #     self.assertEqual(inserted_track_1.id, inserted_track_2.id)
    #     _ = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     self.assertEqual(len(nd.library), 2)
    #     nd.config.skip_duplicate = True

    # def test_add_file_stores_file_namename(self):
    #     """Test the `copy_to_library` config variable."""
    #     nd.config.copy_to_library = True
    #     nd.library.reset(force=True)
    #     inserted_track = nd.library.add_track(file_path="tests/assets/test.wav")
    #     queried_track = nd.library.get_track(inserted_track.id)
    #     self.assertEqual(queried_track.resource.meta["original_filename"], "test.wav")
    #     nd.config.copy_to_library = False

    # def test_add_tracks_adds_all_files_in_folder(self):
    #     """Test the `nd.library.add_tracks()` function."""
    #     nd.library.reset(force=True)
    #     nd.library.add_tracks(path="tests/assets")
    #     results = nd.library.get_tracks()
    #     self.assertEqual(len(results), 3)
    #     results = nd.library.get_tracks(limit=1)
    #     self.assertEqual(len(results), 1)
    #     # try adding again, should update existing
    #     nd.library.add_tracks(path="tests/assets")
    #     results = nd.library.get_tracks()
    #     self.assertEqual(len(results), 3)

    # def test_remove_file_from_library(self):
    #     """Test the `nd.library.remove_track()` function."""
    #     nd.library.reset(force=True)
    #     inserted_track = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     results_before_remove = nd.library.find_tracks(value="Test Artist")
    #     nd.library.remove_track(track_id=inserted_track.id)
    #     results_after_remove = nd.library.find_tracks(value="Test Artist")
    #     self.assertTrue(len(results_before_remove) > len(results_after_remove))
    #     self.assertFalse(os.path.exists(inserted_track.resource.src))

    # def test_remove_track_with_relations_returns_false(self):
    #     """Test removal of tracks with existing relations (without forcing)."""
    #     nd.library.reset(force=True)
    #     inserted_track1 = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     inserted_track2 = nd.library.add_related_track(
    #         file_path="tests/assets/test.wav",
    #         related_track_id=inserted_track1.id,
    #         relationship_type="stem",
    #         meta={"test": "value"},
    #     )
    #     inserted_track3 = nd.library.add_related_track(
    #         file_path="tests/assets/test.wav",
    #         related_track_id=inserted_track1.id,
    #         relationship_type="stem",
    #         meta={"test": "value"},
    #     )

    #     result = nd.library.remove_track(inserted_track1.id, remove_relationships=False)
    #     track_1_after_remove = nd.library.get_track(inserted_track1.id)
    #     self.assertTrue(track_1_after_remove.id == inserted_track1.id)

    #     track_2_after_remove = nd.library.get_track(inserted_track2.id)
    #     self.assertTrue(track_2_after_remove.id == inserted_track2.id)

    #     track_3_after_remove = nd.library.get_track(inserted_track3.id)
    #     self.assertTrue(track_3_after_remove.id == inserted_track3.id)

    #     self.assertFalse(result)

    # def test_remove_track_with_relations_removes_relations(self):
    #     """Test the removal of tracks with relations (with forcing)."""
    #     nd.config.skip_duplicate = False
    #     nd.library.reset(force=True)
    #     inserted_track1 = nd.library.add_track(file_path="tests/assets/test.wav")
    #     inserted_track2 = nd.library.add_related_track(
    #         file_path="tests/assets/test.wav",
    #         related_track_id=inserted_track1.id,
    #         relationship_type="stem",
    #         meta={"test": "value"},
    #     )
    #     inserted_track3 = nd.library.add_related_track(
    #         file_path="tests/assets/test.wav",
    #         related_track_id=inserted_track2.id,
    #         relationship_type="stem",
    #         meta={"test": "value"},
    #     )
    #     inserted_track4 = nd.library.add_track(
    #         file_path="tests/assets/test.wav",
    #     )
    #     inserted_track5 = nd.library.add_track(
    #         file_path="tests/assets/test.wav",
    #     )
    #     inserted_track4.relate_to_track(inserted_track1.id)
    #     inserted_track5.relate_to_track(inserted_track1.id)

    #     # confirm that the related_tracks exist
    #     inserted_track1.refresh()
    #     self.assertTrue(inserted_track1.has_relationship("stem"))

    #     inserted_track2.refresh()
    #     self.assertTrue(inserted_track2.has_relationship("stem"))
    #     inserted_track_2_all_related = nd.library.get_related_tracks(
    #         inserted_track2.id,
    #         direction="both",
    #     )
    #     self.assertEqual(len(inserted_track_2_all_related), 2)

    #     self.assertTrue(inserted_track1.has_related_track(inserted_track4.id))
    #     self.assertTrue(inserted_track1.has_related_track(inserted_track5.id))

    #     inserted_track1_id = inserted_track1.id
    #     result = nd.library.remove_track(inserted_track1_id, remove_relationships=True)
    #     inserted_track1 = nd.library.get_track(inserted_track1_id)

    #     self.assertIsNone(inserted_track1)
    #     self.assertTrue(result)

    #     nd.config.skip_duplicate = True

    # def test_add_collection_adds_collection(self):
    #     """Test the `nd.library.add_collection()` method."""
    #     nd.library.reset(force=True)

    #     test_track_1 = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     test_track_2 = nd.library.add_track(file_path="tests/assets/test.wav")
    #     test_collection = nd.library.add_collection(
    #         track_ids=[test_track_1.id, test_track_2.id],
    #         name="Testcollection",
    #     )
    #     self.assertEqual(test_collection.name, "Testcollection")
    #     retrieved_test_collection = nd.library.get_collection(
    #         collection_id=test_collection.id,
    #     )
    #     self.assertEqual(test_collection.name, retrieved_test_collection.name)
    #     self.assertEqual(
    #         len(test_collection.related_tracks),
    #         len(retrieved_test_collection.related_tracks),
    #     )
    #     rts = [rt.source.id for rt in retrieved_test_collection.related_tracks]
    #     self.assertTrue(test_track_1.id in rts)

    # def test_add_track_to_collection(self):
    #     """Test the adding of tracks to collections."""
    #     nd.library.reset(force=True)
    #     test_track_1 = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     test_track_2 = nd.library.add_track(file_path="tests/assets/test.wav")
    #     test_collection = nd.library.add_collection(
    #         track_ids=[test_track_1.id],
    #         name="Testcollection",
    #     )
    #     self.assertEqual(len(test_collection), 1)
    #     nd.library.add_track_to_collection(
    #         track_id=test_track_2.id,
    #         collection_id=test_collection.id,
    #     )
    #     retrieved_test_collection = nd.library.get_collection(
    #         collection_id=test_collection.id,
    #     )
    #     self.assertEqual(len(retrieved_test_collection), 2)

    # def test_find_collections_by_empty_value(self):
    #     """Test finding collections by empty search value."""
    #     nd.library.reset(force=True)
    #     test_track_1 = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     test_track_2 = nd.library.add_track(file_path="tests/assets/test.wav")
    #     test_collection = nd.library.add_collection(
    #         track_ids=[test_track_1.id, test_track_2.id],
    #         name="Testcollection",
    #     )
    #     test_collection_2 = nd.library.add_collection(
    #         track_ids=[test_track_1.id, test_track_2.id],
    #         name="Testcollection2",
    #     )
    #     retrieved_test_collection = nd.library.find_collections()
    #     self.assertEqual(len(retrieved_test_collection), 2)
    #     self.assertEqual(retrieved_test_collection[0].id, test_collection.id)
    #     self.assertEqual(retrieved_test_collection[1].id, test_collection_2.id)

    # def test_find_collections_by_collection_name(self):
    #     """Test finding collections by name as search value."""
    #     nd.library.reset(force=True)
    #     test_track_1 = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     test_track_2 = nd.library.add_track(file_path="tests/assets/test.wav")
    #     test_collection = nd.library.add_collection(
    #         track_ids=[test_track_1.id, test_track_2.id],
    #         name="Testcollection",
    #     )
    #     nd.library.add_collection(
    #         track_ids=[test_track_1.id, test_track_2.id],
    #         name="iwontbefoundcollection",
    #     )
    #     retrieved_test_collection = nd.library.find_collections("Testc")
    #     self.assertEqual(len(retrieved_test_collection), 1)
    #     self.assertEqual(retrieved_test_collection[0].id, test_collection.id)

    # def test_get_all_collections(self):
    #     """Test getting all collections."""
    #     nd.library.reset(force=True)
    #     test_track_1 = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     test_track_2 = nd.library.add_track(file_path="tests/assets/test.wav")
    #     test_collection = nd.library.add_collection(
    #         track_ids=[test_track_1.id, test_track_2.id],
    #         name="Testcollection",
    #     )
    #     test_collection_2 = nd.library.add_collection(
    #         track_ids=[test_track_1.id, test_track_2.id],
    #         name="Testcollection2",
    #     )
    #     all_collections = nd.library.get_collections()
    #     self.assertEqual(len(all_collections), 2)
    #     self.assertEqual(all_collections[0].id, test_collection.id)
    #     self.assertEqual(all_collections[1].id, test_collection_2.id)

    # def test_remove_collection_without_relationships(self):
    #     """Test removing of collections that have no relationships."""
    #     nd.library.reset(force=True)
    #     test_track_1 = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     test_track_2 = nd.library.add_track(file_path="tests/assets/test.wav")
    #     test_collection = nd.library.add_collection(
    #         track_ids=[test_track_1.id, test_track_2.id],
    #         name="Testcollection",
    #     )
    #     self.assertTrue(
    #         nd.library.remove_collection(
    #             collection_id=test_collection.id,
    #             remove_relationships=False,
    #         ),
    #     )

    # def test_remove_collection_with_relationships_failing(self):
    #     """Test the removing of collections with relationships (without forcing)."""
    #     nd.library.reset(force=True)
    #     test_track_1 = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     test_track_2 = nd.library.add_track(file_path="tests/assets/test.wav")
    #     test_collection_1 = nd.library.add_collection(
    #         track_ids=[test_track_1.id, test_track_2.id],
    #         name="Testcollection1",
    #     )
    #     nd.library.add_related_collection(
    #         track_ids=[test_track_1.id, test_track_2.id],
    #         collection_id=test_collection_1.id,
    #         name="Testcollection2",
    #     )
    #     self.assertFalse(
    #         nd.library.remove_collection(
    #             collection_id=test_collection_1.id,
    #             remove_relationships=False,
    #         ),
    #     )

    # def test_remove_collection_with_relationships_succeeding(self):
    #     """Test the removing of collections with relationships (with forcing)."""
    #     nd.library.reset(force=True)
    #     test_track_1 = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     test_track_2 = nd.library.add_track(file_path="tests/assets/test.wav")
    #     test_collection_1 = nd.library.add_collection(
    #         track_ids=[test_track_1.id, test_track_2.id],
    #         name="Testcollection",
    #     )
    #     nd.library.add_related_collection(
    #         track_ids=[test_track_1.id, test_track_2.id],
    #         collection_id=test_collection_1.id,
    #         name="Testcollection2",
    #     )
    #     self.assertTrue(
    #         nd.library.remove_collection(
    #             collection_id=test_collection_1.id,
    #             remove_relationships=True,
    #         ),
    #     )

    # def test_remove_track_updates_collections(self):
    #     """Test that removing tracks also removes them from relevant collections."""
    #     nd.library.reset(force=True)
    #     test_track_1 = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     test_track_2 = nd.library.add_track(file_path="tests/assets/test.wav")
    #     test_collection = nd.library.add_collection(name="Testcollection")
    #     nd.library.add_track_to_collection(
    #         collection_id=test_collection.id,
    #         track_id=test_track_1.id,
    #     )
    #     nd.library.add_track_to_collection(
    #         collection_id=test_collection.id,
    #         track_id=test_track_2.id,
    #     )

    #     # Remove the first test track
    #     nd.library.remove_track(track_id=test_track_1.id, remove_relationships=True)

    #     # Get the tracks from the collection
    #     test_collection = nd.library.get_collection(collection_id=test_collection.id)

    #     # Assert that the second track was removed and
    #     # positions of other tracks were updated
    #     self.assertIsNotNone(test_collection.related_tracks[0])
    #     self.assertIsNotNone(test_collection.related_tracks[0].relationship_position)
    #     self.assertEqual(test_collection.related_tracks[0].relationship_position, 0)

    # def test_remove_track_from_collection_updates_positions(self):
    #     """Test that removing tracks updates the positions in affected collections."""
    #     nd.library.reset(force=True)
    #     test_track_1 = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     test_track_2 = nd.library.add_track(file_path="tests/assets/test.wav")
    #     test_collection = nd.library.add_collection(name="Testcollection")
    #     nd.library.add_track_to_collection(
    #         collection_id=test_collection.id,
    #         track_id=test_track_1.id,
    #         position=0,
    #     )
    #     nd.library.add_track_to_collection(
    #         collection_id=test_collection.id,
    #         track_id=test_track_2.id,
    #         position=1,
    #     )

    #     # Remove the first track from the collection
    #     nd.library.remove_track_from_collection(
    #         track_id=test_track_1.id,
    #         collection_id=test_collection.id,
    #     )

    #     # Get the tracks from the collection
    #     test_collection = nd.library.get_collection(collection_id=test_collection.id)

    #     # Assert that the second track was removed and
    #     # positions of other tracks were updated
    #     self.assertIsNotNone(test_collection.related_tracks[0])
    #     self.assertIsNotNone(test_collection.related_tracks[0].relationship_position)
    #     self.assertEqual(test_collection.related_tracks[0].relationship_position, 0)

    # def test_library_get_tracks_stream(self):
    #     """Test the `stream_mode` functionality of Nendo."""
    #     # with stream_chunk_size > 1, the generator should return
    #     # chunks (lists) of tracks
    #     nd.config.skip_duplicate = False
    #     nd.config.stream_mode = True
    #     nd.config.stream_chunk_size = 4
    #     nd.library.reset(force=True)
    #     nd.library.add_track(file_path="tests/assets/test.wav")
    #     nd.library.add_track(file_path="tests/assets/test.wav")
    #     nd.library.add_track(file_path="tests/assets/test.wav")
    #     nd.library.add_track(file_path="tests/assets/test.wav")
    #     nd.library.add_track(file_path="tests/assets/test.wav")
    #     tracks_iterator = nd.library.get_tracks()
    #     self.assertEqual(type(tracks_iterator), GeneratorType)
    #     i = 0
    #     for chunk in tracks_iterator:
    #         self.assertEqual(type(chunk), list)
    #         self.assertEqual(type(chunk[0]), NendoTrack)
    #         if i == 0:
    #             self.assertEqual(len(chunk), 4)
    #         else:
    #             self.assertEqual(len(chunk), 1)
    #         i += 1
    #     # with stream_chunk_size == 1, the generator should return
    #     # individual tracks
    #     nd.config.stream_chunk_size = 1
    #     tracks_iterator = nd.library.get_tracks()
    #     for chunk in tracks_iterator:
    #         self.assertEqual(type(chunk), NendoTrack)
    #     nd.config.skip_duplicate = True
    #     nd.config.stream_mode = False
    #     nd.config.stream_chunk_size = 1

    # def test_get_track_or_collection(self):
    #     """Test the `nd.library.get_track_or_collection()` method."""
    #     nd.library.reset(force=True)
    #     test_track = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     test_collection = nd.library.add_collection(
    #         track_ids=[test_track.id],
    #         name="Testcollection",
    #     )
    #     result = nd.library.get_track_or_collection(target_id=test_track.id)
    #     self.assertTrue(isinstance(result, NendoTrack))
    #     self.assertEqual(result.id, test_track.id)
    #     result = nd.library.get_track_or_collection(target_id=test_collection.id)
    #     self.assertTrue(isinstance(result, NendoCollection))
    #     self.assertEqual(result.id, test_collection.id)

    # def test_store_blob(self):
    #     """Test the `nd.library.store_blob()` function."""
    #     nd.library.reset(force=True)

    #     test_blob = nd.library.store_blob(file_path="tests/assets/test.wav")
    #     test_blob_2 = nd.library.store_blob(file_path="tests/assets/test.mp3")
    #     self.assertIsNone(test_blob.data)
    #     self.assertIsNone(test_blob_2.data)
    #     self.assertTrue(os.path.isfile(test_blob.resource.src))
    #     self.assertTrue(os.path.isfile(test_blob_2.resource.src))

    # def test_store_blob_from_bytes(self):
    #     """Test the storing of blobs from `bytes` objects."""
    #     nd.library.reset(force=True)

    #     data_1 = b"test_blob"
    #     data_2 = b"test_blob_2"

    #     test_blob = nd.library.store_blob_from_bytes(data=data_1)
    #     test_blob_2 = nd.library.store_blob_from_bytes(data=data_2)
    #     self.assertIsNone(test_blob.data)
    #     self.assertIsNone(test_blob_2.data)
    #     self.assertTrue(os.path.isfile(test_blob.resource.src))
    #     self.assertTrue(os.path.isfile(test_blob_2.resource.src))

    # def test_get_blob(self):
    #     """Test the retrieval of blobs using `nd.library.get_blob()`."""
    #     nd.library.reset(force=True)

    #     data_1 = b"test_blob"
    #     data_2 = b"test_blob_2"

    #     test_blob = nd.library.store_blob_from_bytes(data=data_1)
    #     test_blob_2 = nd.library.store_blob_from_bytes(data=data_2)

    #     test_blob = nd.library.load_blob(blob_id=test_blob.id)
    #     self.assertEqual(test_blob.data, data_1)

    #     test_blob_2 = nd.library.load_blob(blob_id=test_blob_2.id)
    #     self.assertEqual(test_blob_2.data, data_2)
    #     self.assertTrue(os.path.isfile(test_blob.resource.src))
    #     self.assertTrue(os.path.isfile(test_blob_2.resource.src))

    # def test_remove_blob(self):
    #     """Test the removal of blobs using `nd.library.remove_blob()`."""
    #     nd.library.reset(force=True)

    #     data_1 = b"test_blob"
    #     data_2 = b"test_blob_2"

    #     test_blob = nd.library.store_blob_from_bytes(data=data_1)
    #     test_blob_2 = nd.library.store_blob_from_bytes(data=data_2)

    #     test_blob = nd.library.load_blob(blob_id=test_blob.id)
    #     self.assertEqual(test_blob.data, data_1)

    #     test_blob_2 = nd.library.load_blob(blob_id=test_blob_2.id)
    #     self.assertEqual(test_blob_2.data, data_2)
    #     self.assertTrue(os.path.isfile(test_blob.resource.src))
    #     self.assertTrue(os.path.isfile(test_blob_2.resource.src))

    #     nd.library.remove_blob(blob_id=test_blob.id)
    #     nd.library.remove_blob(blob_id=test_blob_2.id)
    #     self.assertFalse(os.path.isfile(test_blob.resource.src))
    #     self.assertFalse(os.path.isfile(test_blob_2.resource.src))

    # def test_verify_delete_and_ignore(self):
    #     """Test the `nd.library.verify()` method."""
    #     nd.library.reset(force=True)
    #     # test verification of orphaned DB entries
    #     test_track_1 = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     nd.library.storage_driver.remove_file(
    #         file_name=test_track_1.resource.file_name,
    #         user_id=nd.config.user_id,
    #     )
    #     # first, ignore inconsistency
    #     nd.library.verify(action="i", user_id=nd.config.user_id)
    #     self.assertEqual(
    #         nd.library.get_track(track_id=test_track_1.id).id,
    #         test_track_1.id,
    #     )
    #     # next, remove track upon detected inconsistency
    #     nd.library.verify(action="r", user_id=nd.config.user_id)
    #     self.assertEqual(len(nd.library), 0)

    #     # test verification of orphaned files
    #     test_track_1 = nd.library.add_track(file_path="tests/assets/test.mp3")
    #     nd.library.remove_track(track_id=test_track_1.id, remove_resources=False)
    #     # first, ignore inconsistency
    #     nd.library.verify(action="i", user_id=nd.config.user_id)
    #     self.assertEqual(
    #         nd.library.storage_driver.file_exists(
    #             file_name=test_track_1.resource.file_name,
    #             user_id=nd.config.user_id,
    #         ),
    #         True,
    #     )
    #     # next, remove track upon detected inconsistency
    #     nd.library.verify(action="r", user_id=nd.config.user_id)
    #     self.assertEqual(
    #         nd.library.storage_driver.file_exists(
    #             file_name=test_track_1.resource.file_name,
    #             user_id=nd.config.user_id,
    #         ),
    #         False,
    #     )


if __name__ == "__main__":
    unittest.main()
