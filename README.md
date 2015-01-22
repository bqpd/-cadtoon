# cadtoons

cadtoons is a library that turns labeled [SVG](https://en.wikipedia.org/wiki/Scalable_Vector_Graphics) drawings into something that can be reshaped according to changing parameters. Though the library is somewhat useful for simple 2D manufacturing, its purpose is to make something like a [Chernoff face](https://en.wikipedia.org/wiki/Chernoff_face) for visualizing many-variable optimizations of engineering designs.

**Example sandbox pages: [Airplane](http://bqpd.github.io/cadtoons/flightconditions.html) |  [Quadrotor](http://bqpd.github.io/cadtoons/quadrotor.html)**

## How to use cadtoons

  1. Make an SVG drawing
    * [Inkscape](http://www.inkscape.org) is an excellent tool for this
  2. Give new and meaningful `id`s to the groups and paths that you want to control
    * in Inkscape do this with the "Object Properties" option, found in the context and Object menus or by pressing Ctrl-Shift-O
  3. Run the `cadtoon.py` script on your new SVG
    * e.g. `./cadtoon.py example.svg`
      * If you run into any errors, please [add an issue](https://github.com/bqpd/cadtoons/issues/new) to this repository!
      * Known bugs:
        1. `cadtoon.py` deletes absolute arcs ("A" commands)
          * Solution: delete the absolute arcs if possible, or use the path editor to convert them to relative arcs.
        2. Translation on named groups that have been rotated follows the axes of their rotation, not x and y
          * Sometimes, this is a boon, allowing easy translation at other angles. If you want x/y motion, though, you'll need to remove that rotation...
          * For a group the easiest way to do this is by ungrouping, cutting the group elements, and pasting them back in place (Ctrl-Alt-V). Then regroup and rename the group
          * For a path, cutting it and pasting it in place (Ctrl-Alt-V) should do the trick.
  4. Open the newly created "sandbox" page that cadtoons created at e.g. `example.html`
    * Play around with the sliders (see above for links to examples)
    * Add constraints to link elements so that they move together
  5. (coming soon) Import the ractive-ready SVG (e.g. `example-ractive.svg`) into a [gpkit](https://github.com/convexopt/gpkit) model


## cadtoons Dependencies

cadtoons uses the lovely [Ractive.js](ractivejs.org) to animate SVGs.
