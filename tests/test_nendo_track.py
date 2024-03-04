# -*- encoding: utf-8 -*-
"""Tests for the Nendo Core class `NendoTrack`."""

import os
import unittest
import uuid
from unittest.mock import Mock

import numpy as np
import sounddevice

from nendo import Nendo, NendoConfig, NendoTrack
from nendo.schema.core import NendoRelationship, NendoResource

nd = Nendo(
    config=NendoConfig(
        log_level="DEBUG",
        library_plugin="default",
        library_path="tests/library",
    ),
)


class NendoTrackTests(unittest.TestCase):
    """Unit test class for testing the NendoTrack class."""

    def test_has_relationship(self):
        """Test the `NendoTrack.has_relationship()` method."""
        resource = NendoResource(
            file_path="tests/assets/",
            file_name="test.wav",
            resource_type="audio",
            meta={
                "original_filename": os.path.basename("tests/assets/test.wav"),
            },
        )
        track = NendoTrack(id=uuid.uuid4(), user_id=uuid.uuid4(), resource=resource)

        relationship = NendoRelationship(
            id=uuid.uuid4(),
            source_id=track.id,
            target_id=uuid.uuid4(),
            relationship_type="stem",
            meta={},
        )

        track.related_tracks = [relationship]

        self.assertTrue(track.has_relationship("stem"))
        self.assertFalse(track.has_relationship("outpainting"))

    def test_is_silent(self):
        """Test the `NendoTrack.is_silent()` method."""
        nd.library.reset(force=True)
        track = nd.library.add_track(file_path="tests/assets/test.wav")
        self.assertFalse(track.is_silent())
        silent_track = nd.library.add_track(file_path="tests/assets/silence.mp3")
        self.assertTrue(silent_track.is_silent())

    def test_signal_sr_properties_exist(self):
        """Test the `NendoTrack.signal` and `NendoTrack.sr` properties."""
        nd.library.reset(force=True)
        track = nd.library.add_track(file_path="tests/assets/test.wav")
        self.assertEqual(track.signal.shape, (2, 2676096))
        self.assertEqual(track.sr, 22050)

    def test_overlay(self):
        """Test the `NendoTrack.overlay()` method."""
        nd.library.reset(force=True)
        t1 = nd.library.add_track(file_path="tests/assets/test.wav")
        t2 = nd.library.add_track(file_path="tests/assets/test.mp3")

        new_track = t1.overlay(t2)

        self.assertIsNotNone(new_track)
        self.assertEqual(new_track.sr, t1.sr)
        self.assertEqual(new_track.signal.shape, t1.signal.shape)

    def test_slice(self):
        """Test the `NendoTrack.slice()` method."""
        nd.library.reset(force=True)
        t1 = nd.library.add_track(file_path="tests/assets/test.wav")

        sliced_signal = t1.slice(start=0, end=10)

        self.assertIsNotNone(sliced_signal)
        self.assertEqual(sliced_signal.shape, (2, 220500))

    def test_play(self):
        """Test the playback of `NendoTrack`s."""
        nd.library.reset(force=True)
        sounddevice.play = Mock()
        sounddevice.wait = Mock()
        track = nd.library.add_track(file_path="tests/assets/test.wav")
        track.play()

        sounddevice.play.assert_called_once()
        sounddevice.wait.assert_called_once()

        # manually asserting call args because mock.assert_called_once_with()
        # doesn't work with numpy arrays
        np.testing.assert_array_equal(sounddevice.play.call_args[0][0], track.signal.T)
        self.assertEqual(sounddevice.play.call_args[1]["samplerate"], track.sr)
        self.assertEqual(sounddevice.play.call_args[1]["loop"], False)

    def test_loop(self):
        """Test the looping of `NendoTrack`s."""
        nd.library.reset(force=True)
        sounddevice.play = Mock()
        sounddevice.wait = Mock()
        track = nd.library.add_track(file_path="tests/assets/test.wav")
        track.loop()

        sounddevice.play.assert_called_once()
        sounddevice.wait.assert_called_once()

        # manually asserting call args because mock.assert_called_once_with()
        # doesn't work with numpy arrays
        np.testing.assert_array_equal(sounddevice.play.call_args[0][0], track.signal.T)
        self.assertEqual(sounddevice.play.call_args[1]["samplerate"], track.sr)
        self.assertEqual(sounddevice.play.call_args[1]["loop"], True)

    def test_get_relationship_by_id(self):
        """Test the accessing of relationships of `NendoTrack`s by their id."""
        resource = NendoResource(
            file_path="tests/assets/",
            file_name="test.wav",
            resource_type="audio",
            meta={
                "original_filename": os.path.basename("tests/assets/test.wav"),
            },
        )
        track = NendoTrack(id=uuid.uuid4(), user_id=uuid.uuid4(), resource=resource)

        relationship_1_id = uuid.uuid4()
        relationship_1 = NendoRelationship(
            id=uuid.uuid4(),
            source_id=track.id,
            target_id=relationship_1_id,
            relationship_type="stem",
            meta={},
        )

        relationship_2_id = uuid.uuid4()
        relationship_2 = NendoRelationship(
            id=uuid.uuid4(),
            source_id=track.id,
            target_id=relationship_2_id,
            relationship_type="stem",
            meta={},
        )

        track.related_tracks = [relationship_1, relationship_2]


if __name__ == "__main__":
    unittest.main()
