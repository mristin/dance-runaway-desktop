*********************
dance-runaway-desktop
*********************

Run away dancing the mat.

.. image:: https://github.com/mristin/dance-runaway-desktop/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/mristin/dance-runaway-desktop/actions/workflows/ci.yml
    :alt: Continuous integration

.. image:: https://media.githubusercontent.com/media/mristin/dance-runaway-desktop/main/screenshot.gif
    :alt: Screenshot

Installation
============
Download and unzip a version of the game from the `Releases`_.

.. _Releases: https://github.com/mristin/dance-runaway-desktop/releases

Running
=======
You need to connect the dance mat *before* starting the game.

Run ``dance-runaway.exe`` (in the directory where you unzipped the game).

If you have multiple joysticks attached, the first joystick is automatically selected, and assumed to be the dance mat.

If the first joystick does not correspond to your dance mat, list the available joysticks with the following command in the command prompt:

.. code-block::

    dance-runaway.exe --list_joysticks

You will see the names and unique IDs (GUIDs) of your joysticks.
Select the joystick that you wish by providing its GUI.
For example:

.. code-block::

    dance-runaway.exe -joystick 03000000790000001100000000000000

Which dance mat to use?
=======================
We used an unbranded dance mat which you can order, say, from Amazon:
https://www.amazon.com/OSTENT-Non-Slip-Dancing-Dance-Compatible-PC/dp/B00FJ2KT8M

Please let us know by `creating an issue`_ if you tested the game with other mats!

.. _creating an issue: https://github.com/mristin/dance-runaway-desktop/issues/new

Acknowledgments
===============
Pirate images come from: https://opengameart.org/content/pirate-character-sprites

Troll images are from: https://opengameart.org/content/2d-game-trolls-sprite

Forest scene images are from: https://opengameart.org/content/cartoon-forest-2d-backgrounds
