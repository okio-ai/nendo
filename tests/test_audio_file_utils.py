# -*- encoding: utf-8 -*-
"""Unit tests for testing the AudioFileUtils class."""

import unittest
from unittest.mock import Mock

import numpy as np
import sounddevice

from nendo.utils import AudioFileUtils, play_signal


class TestingAudioFileUtils(unittest.TestCase):
    """Unit test class for testing the AudioFileUtils class."""

    def test_supported_files(self):
        """Test the supported fileypes."""
        audio_utils = AudioFileUtils()

        self.assertTrue(audio_utils.is_supported_filetype("test.WAV"))
        self.assertTrue(audio_utils.is_supported_filetype("test.mp3"))
        self.assertTrue(audio_utils.is_supported_filetype("test.aiff"))
        self.assertTrue(audio_utils.is_supported_filetype("test.flac"))
        self.assertTrue(audio_utils.is_supported_filetype("test.ogg"))
        self.assertFalse(audio_utils.is_supported_filetype("test.m4a"))

    def test_unsupported_files(self):
        """Test an unsupported filetype."""
        audio_utils = AudioFileUtils()
        self.assertFalse(audio_utils.is_supported_filetype("test.wma"))

    def test_play_signal(self):
        """Test playing the signal."""
        sounddevice.play = Mock()
        sounddevice.wait = Mock()

        signal = np.array([0, 1, 2, 3, 4])
        sr = 4
        play_signal(signal, sr)

        sounddevice.play.assert_called_once()
        sounddevice.wait.assert_called_once()

        # manually asserting call args because mock.assert_called_once_with()
        # doesn't work with numpy arrays
        np.testing.assert_array_equal(sounddevice.play.call_args[0][0], signal.T)
        self.assertEqual(sounddevice.play.call_args[1]["samplerate"], sr)
        self.assertEqual(sounddevice.play.call_args[1]["loop"], False)
