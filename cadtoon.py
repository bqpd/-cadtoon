#!/usr/bin/env python

import sys
import xmltodict
import numpy as np
from string import Template
import os.path

args = sys.argv
if len(args) != 2:
    print "    ERROR: usage is %s $FILENAME.SVG" % args[0]
    sys.exit(0)
else:
    title = args[1]
    if title[-4:] != ".svg":
        print "    ERROR: usage is %s $FILENAME.SVG" % args[0]
        sys.exit(0)
    else:
        title = title[:-4]

scaling_template = Template("matrix({{$cl.scalex * $cl.scale}}, 0, 0, {{$cl.scaley * $cl.scale}}, {{$cl.x + $centrex * (1-$cl.scalex * $cl.scale)}}, {{$cl.y + $centrey * (1-$cl.scaley * $cl.scale)}})")

idlist = []

def remove_attrs(group):
    for key in group:
        for attr_to_rm in ["xmlns", "sodipodi", "inkscape", "defs", "metadata"]:
            if attr_to_rm in key:
                group.pop(key)
#                print "Removed", key
                break

def check_id(group):
    if not "@id" in group:
        return None
    id = group.pop("@id")
    ld = id.find("-")
    rd = id.rfind("-")
    if ld != rd or "layer" in id or "svg" in id:
        return None
    if ld == -1:
        cl = id
    else:
        cl = id[:ld]
    return cl

def updateBounds(bounds, pos, other_bounds = None):
    x, y = pos
    if other_bounds is None:
        if bounds["x"][0] is None:
            bounds["x"] = [x, x]
            bounds["y"] = [y, y]
        if bounds["x"][0] > x:
            bounds["x"][0] = x
        if bounds["x"][1] < x:
            bounds["x"][1] = x
        if bounds["y"][0] > y:
            bounds["y"][0] = y
        if bounds["y"][1] < y:
            bounds["y"][1] = y
    else:
        lx = x + other_bounds["x"][0]
        ux = x + other_bounds["x"][1]
        ly = y + other_bounds["y"][0]
        uy = y + other_bounds["y"][1]
        if bounds["x"][0] is None:
            bounds["x"] = [lx, ux]
            bounds["y"] = [ly, uy]
        if bounds["x"][0] > lx:
            bounds["x"][0] = lx
        if bounds["x"][1] < ux:
            bounds["x"][1] = ux
        if bounds["y"][0] > ly:
            bounds["y"][0] = ly
        if bounds["y"][1] < uy:
            bounds["y"][1] = uy

def applyTranslation(group, pos):
    if "@transform" in group:
        transform = group["@transform"][:-1].split("(")
        ttype = transform[0]
        tvals = map(float, transform[1].split(","))
        if ttype == "matrix":
            delta = np.array(tvals[4:])
        elif ttype == "translate":
            delta = np.array(tvals)
        else:
            delta = np.array([0.0, 0.0])
    else:
        delta = np.array([0.0, 0.0])
    return pos + delta


def groupWrap(new_class, group, transform="scale(1)"):
    if "@transform" in group:
        gtrans = group.pop("@transform")
        newgroup = {"g": group.copy(), "@transform":gtrans}
        group.update(newgroup)
        for key in group:
            if key not in ["g", "@transform"]:
                del group[key]
        group["g"]["@class"] = new_class
        group["g"]["@transform"] = transform
    else:
        group["@class"] = new_class
        group["@transform"] = transform

def recurse_down(group, bounds = {"x": [None, None], "y": [None, None]}, orig=np.array([0.0,0.0])):
    remove_attrs(group)
    group_new_class = check_id(group)
    if group_new_class:
        orig = np.array([0.0, 0.0])
        bounds = {"x": [None, None], "y": [None, None]}
    else:
        orig = applyTranslation(group, orig)

    path_new_class = None
    if "path" in group:
        paths = group["path"]
        if type(paths) != list: paths = [paths]
        for p, path in enumerate(paths):
            remove_attrs(path)
            path_new_class = check_id(path)
            pos = np.array([0.0, 0.0])
            path_bounds = {"x": [None, None], "y": [None, None]}
            d = path["@d"].split()
            lastcmd = None
            lastcmdidx = None
            for i, el in enumerate(d):
                if el in "mMCcaAlz":
                    lastcmd = el
                    lastcmdidx = i
                elif lastcmd == "C":
                    #print "Removing C command"
                    if i == (lastcmdidx + 1):
                        d[i-1] = ""
                    d[i] = ""
                else:
                    el = el.split(",")
                    el = map(float, el)
                    if lastcmd == "m":
                        pos += np.array(el);
                    elif lastcmd == "c":
                        if (i-lastcmdidx)%3 == 0:
                            pos += np.array(el)
                    elif lastcmd == "a":
                        # rx,ry
                        # x-axis-rotation (leave untouched)
                        # large-arc-flag (leave untouched)
                        # sweep-flag (leave untouched)
                        if i == lastcmdidx + 5:
                            # x,y
                            pos += np.array(el)
                    elif lastcmd == "l":
                        pos += np.array(el)
                    else:
                        print "Unknown command", lastcmd
                    updateBounds(path_bounds, pos)
            path["@d"] = " ".join(d)
            updateBounds(bounds, orig, path_bounds)
            if path_new_class:
                if "@transform" in path:
                    newg = {"path": path, "@transform": path["@transform"]}
                    if "g" in group:
                        if type(group["g"]) == list:
                            group["g"].append(newg)
                        else:
                            group["g"] = [group["g"], newg]
                    else:
                        group["g"] = newg
                    if type(group["path"]) != list:
                        del group["path"]
                    else:
                        group["path"].remove(path)
                if path_bounds["x"][0] is None:
                    path["@transform"] = scaling_template.substitute(cl=path_new_class, centrex=0, centrey=0)
                else:
                    path["@transform"] = scaling_template.substitute(cl=path_new_class, centrex=(path_bounds["x"][1] + path_bounds["x"][0])/2.0, centrey=(path_bounds["y"][1] + path_bounds["y"][0])/2.0)
                path["@class"] = path_new_class
                if not path_new_class in idlist:
                    idlist.append(path_new_class)
                print "path", path_new_class
    if "g" in group:
        if type(group["g"]) != list:
            gs = [group["g"]]
        else:
            gs = group["g"]
        for g in gs:
            bounds = recurse_down(g, bounds, orig)
    if group_new_class:
        if bounds["x"][0] is None:
            transform = scaling_template.substitute(cl=path_new_class, centrex=0, centrey=0)
        else:
            transform = scaling_template.substitute(cl=group_new_class, centrex=(bounds["x"][1] + bounds["x"][0])/2.0, centrey=(bounds["y"][1] + bounds["y"][0])/2.0)
        groupWrap(group_new_class, group, transform)
        if not group_new_class in idlist:
            idlist.append(group_new_class)
        print "g", group_new_class
    return bounds

with open(title+".svg", 'r') as file:
    doc = xmltodict.parse(file.read())

svg = doc['svg']
w, h = map(float, [svg["@width"], svg["@height"]])
topg = {"g": svg["g"].copy()}
topg["@transform"] = "scale(%.2f)" % min(300.0/w, 300.0/h)
svg["@width"], svg["@height"] = "300", "300"
svg["g"] = topg
recurse_down(svg)
svgtxt = xmltodict.unparse(doc, pretty=True)

with open(title+"-ractive.svg", "w") as file:
    file.write(svgtxt)

# ractive playground
html_template = Template("""<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <title> $title | CADtoon</title>
  <link href='http://fonts.googleapis.com/css?family=Roboto:400,100,100italic,300,300italic,400italic,500,500italic,700,700italic,900,900italic' rel='stylesheet' type='text/css'>
  <style>
    body {
        font-family: "Roboto";
        background: white;
    }

    td {
        padding: 1em;
        text-align: right;
    }

    .left {
        position: fixed;
        left: 40px;
        width: 480px;
        margin: 0 auto;
    }

    .right {
        position: absolute;
        left: 560px;
        top: 60px;
    }

    h1 {
        font-size: 3em;
    }

    h2 {
        font-size: 2em;
    }

    .note {
        margin-top: -1.5em;
    }

    #constraints {
        width: 100%;
        height: 30em;
        font-family: monospace;
    }

    .num {
        font-family: monospace;
        width: 40px;
        float: right;
        padding-top: 5px;
        text-align: left;
        padding-left: 5px;
    }
  </style>
</head>

<body>
  <div id='ractivecontainer'></div>
<script id='ractivetemplate' type='text/ractive'>
  <div class="left">
  <h1>  $title </h1><br><br><br>
$svgtxt
</div><div class="right">
<table id="controls" style="margin: 0 auto;">
$controls
</table>
<h2> constraints </h2>
<div class="note">access variables by <tt>$title.id.attribute</tt>, e.g.:<br>    <tt>fuel.wingrect.scaley = 1 - fuel.wingtaper.scaley</tt></div>
<textarea id="constraints" onchange="updateCbox();">$constraints</textarea>
</div>
  </script>
  <script src='http://cdn.ractivejs.org/latest/ractive.min.js'></script>
  <script>
var $title = {
$init
      }

var cbox = null

var updateCbox = function () {
    if (!constraining) {
        constraining = true;
        try {
            eval(cbox.value)
            cbox.style.backgroundColor = "#fff"
        }
        catch(e) { cbox.style.backgroundColor = "#fdd" }
        constraining = false;
    }
}

      var constraining = false;

        var ractive = new Ractive({
          el: 'ractivecontainer',
          template: '#ractivetemplate',
          magic: true,
          data: $title,
        onchange: updateCbox
        });

    var cbox = document.getElementById("constraints")

    updateCbox()
  </script>
</body>
</html>
""")

gpkit_template = Template("""<div id='ractivecontainer'></div>
<script id='ractivetemplate' type='text/ractive'>
$svgtxt
<div style="text-align: right; font-weight: 700; font-size: 2em;">{{infeasibilitywarning}}</div>
    </script>
    <!-- <script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.3/jquery.min.js"></script> -->
    <script>
    var $title = {
infeasibilitywarning: "",
$init
      }
$dollar.getScript('http://cdn.ractivejs.org/latest/ractive.min.js', function () {
var ractive = new Ractive({
          el: 'ractivecontainer',
          template: '#ractivetemplate',
          magic: true,
          data: $title
        }) })
</script>""")

controls_template = Template("""
    <tr><td>
        <h2> $id </h2></td><td>
        scale <input value='{{$id.scale}}' type="range" min="0" max="2" step="0.05"><div class="num">{{Math.round(100*$id.scale)/100}}</div><br>
        scalex <input value='{{$id.scalex}}' type="range" min="0" max="2" step="0.05"><div class="num">{{Math.round(100*$id.scalex)/100}}</div><br>
        scaley <input value='{{$id.scaley}}' type="range" min="0" max="2" step="0.05"><div class="num">{{Math.round(100*$id.scaley)/100}}</div><br>
        x <input value='{{$id.x}}' type="range" min="-150" max="150" step="1"><div class="num">{{Math.round(100*$id.x)/100}}</div><br>
        y <input value='{{$id.y}}' type="range" min="-150" max="150" step="1"><div class="num">{{Math.round(100*$id.y)/100}}</div><br>
    </td></tr>""")
init_template = Template("$id: {scalex: 1, scaley: 1, scale: 1, x:0, y:0},")

idlist = sorted(idlist)
htmlcontrols = "\n".join([controls_template.substitute(id=i) for i in idlist])
htmlinit = "\n".join([init_template.substitute(id=i) for i in idlist])

svgtxt = svgtxt[svgtxt.index("\n")+1:]

if os.path.isfile(title+".constraints"):
    with open(title+".constraints", 'r') as file:
        constraints = file.read()
else:
    constraints = ""


html = html_template.substitute(title=title,
                                svgtxt=svgtxt,
                                constraints=constraints,
                                controls=htmlcontrols,
                                init=htmlinit)

gpkit_html = gpkit_template.substitute(title=title, svgtxt=svgtxt, init=htmlinit, dollar="$")

with open(title+".html", "w") as file:
    file.write(html)

with open(title+".gpkit", "w") as file:
    file.write(gpkit_html)
