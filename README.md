<p align="center">
  <a href="https://github.com/okio-ai/nendo"><img src="https://okio.ai/docs/assets/nendo_core_logo.png" width="750" alt="Nendo Core"></a>
</p>

<p align="center">
    <em>The AI audio tool suite for developers, powering next-gen audio applications.</em>
</p>

<p align="center">
<a href="https://okio.ai" target="_blank">
    <img src="https://img.shields.io/website/https/okio.ai" alt="Website">
</a>
<a href="https://github.com/okio-ai/nendo/actions/workflows/test.yml" target="_blank">
    <img src="https://github.com/okio-ai/nendo/actions/workflows/test.yml/badge.svg" alt="Test">
</a>
<a href="https://coverage-badge.samuelcolvin.workers.dev/redirect/okio-ai/nendo" target="_blank">
    <img src="https://coverage-badge.samuelcolvin.workers.dev/okio-ai/nendo.svg" alt="Coverage">
</a>
<a href="https://coverage-badge.samuelcolvin.workers.dev/redirct/okio-ai/nendo" target="_blank">
    <img src="" alt="">
</a>
<a href="https://pypi.org/project/nendo" target="_blank">
    <img src="https://img.shields.io/pypi/v/nendo?color=%2334D058&label=pypi%20package" alt="Package version">
</a>
<a href="https://opensource.org/licenses/MIT" target="_blank">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
</a>
<a href="https://discord.gg/gaZMZKzScj" target="_blank">
    <img src="https://dcbadge.vercel.app/api/server/XpkUsjwXTp?compact=true&style=flat" alt="Discord">
</a>
<a href="https://twitter.com/okio_ai" target="_blank">
    <img src="https://img.shields.io/twitter/url/https/twitter.com/okio_ai.svg?style=social&label=Follow%20%40okio_ai" alt="Twitter">
</a>
</p>

---

**Website**: <a href="https://okio.ai/" target="_blank">okio.ai</a>

**Documentation**: <a href="https://okio.ai/docs" target="_blank">okio.ai/docs</a>

**Nendo Platform**: <a href="https://github.com/okio-ai/Nendo-Platform" target="_blank">Repository</a>

---

Nendo core is the AI audio tool suite allowing you to effortlessly develop audio apps that amplify efficiency & creativity across all aspects of audio production.

**[Features](#features)** - **[Requirements](#requirements)** - **[Installation](#installation)** - **[Usage](#usage)** - **[Plugins](#plugins)** - **[Contributing](#contributing)**

## Features

- Easy to use, lightweight framework to develop AI audio applications fast.
- Integrated essentials for audio processing and library management.
- An extensible plugin architecture and growing ecosystem of AI Audio plugins.
- Easily combinable tools that together address a wide range of use cases.
- Support for storing, managing and retrieving embedding vectors.

## Requirements

**Nendo core requires Python version 3.8, 3.9 or 3.10.**

> It is recommended to use a [virtual environment](https://docs.python.org/3/library/venv.html) for installing nendo core, in order to avoid dependency conflicts. You can use your favorite virtual environment management system, like [conda](https://docs.conda.io/en/latest/), [poetry](https://python-poetry.org/), or [pyenv](https://github.com/pyenv/pyenv) for example.

Furthermore, the following software packages need to be installed in your system:

- **Ubuntu**: `sudo apt-get install ffmpeg libsndfile1 libportaudio2`
- **Mac OS**: `brew install ffmpeg libsndfile portaudio`
- **Windows**

    > Windows support is currently under development. For the time being, we highly recommend using [Windows Subsystem for Linux](https://learn.microsoft.com/en-us/windows/wsl/install) and then following the linux instructions. If you still want to try to get Nendo Core to work natively on Windows, you will need to install the following software packages: [ffmpeg](https://ffmpeg.org/download.html), [libsndfile](https://github.com/libsndfile/libsndfile), and [portaudio](https://files.portaudio.com/download.html)

## Installation

You can install Nendo Core directly via `pip`:

```bash
pip install nendo
```

Then you can run nendo in your python shell, notebook or application as follows:

```python
from nendo import Nendo

nendo = Nendo()
```

... and just like that, you're ready to go! Now, there are multiple ways to configure Nendo, refer to the [relevant documentation pages](https://okio.ai/docs/usage/config/) for more information.

## Usage

For example, [install the musicgen nendo plugin](https://github.com/okio-ai/nendo_plugin_musicgen#requirements).

And then run it using nendo:

```python
from nendo import Nendo

nd = Nendo(plugins=["nendo_plugin_musicgen"])
songs = nd.plugins.musicgen(prompt="funky 70s disco", bpm=120)
songs[0].export("funky_disco.mp3")
```

Please refer to the [documentation](https://okio.ai/docs/usage/) to learn more about how to use nendo.

## Plugins

Nendo thrives on its rich [plugin](https://okio.ai/docs/plugins) ecosystem. There are plugins for many different audio processing tasks and the list is growing:

- Audio Generation
- Source Separation
- Audio Analysis
- Voice Generation
- Midi Generation
- Audio Transcription
- Audio Post-Processing
- Audio Quantization
- Audio Loop-Extraction

If you want to develop your own plugin for nendo, consult the [plugin development documentation](https://okio.ai/docs/development/plugindev/), you'll be surprised how simple it is.

## Contributors

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://breathdance.net"><img src="https://avatars.githubusercontent.com/u/5659844?v=4" width="100px;" alt="Felix Lorenz"/><br /><sub><b>Felix Lorenz</b></sub></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/aaronabebe"><img src="https://avatars.githubusercontent.com/u/17432850?v=4" width="100px;" alt="Aaron Abebe"/><br /><sub><b>Aaron Abebe</b></sub></td>
      <td align="center" valign="top" width="14.28%"><a href="https://samim.io"><img src="https://avatars.githubusercontent.com/u/2211475?v=4" width="100px;" alt="Samim"/><br /><sub><b>Samim</b></sub></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/shiehn"><img src="https://avatars.githubusercontent.com/u/826261?v=4" width="100px;" alt="Steve Hiehn"/><br /><sub><b>Steve Hiehn</b></sub></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/JLenzy"><img src="https://avatars.githubusercontent.com/u/64747969?v=4" width="100px;" alt="Julian Lenz"/><br /><sub><b>Julian Lenz</b></sub></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/philibb"><img src="https://avatars.githubusercontent.com/u/23077713?v=4" width="100px;" alt="Philipp Braun"/><br /><sub><b>Philipp Braun</b></sub></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/M-HO"><img src="https://avatars.githubusercontent.com/u/4912712?v=4" width="100px;" alt="Michal Ho"/><br /><sub><b>Michal Ho</b></sub></td>
    </tr>
  </tbody>
</table>
<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

Want to be part of the AI audio revolution? All contributions are welcome! Check out our [contribution guide](https://okio.ai/docs/contributing) to learn more about how to develop with and for nendo.
