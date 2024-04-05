# A Quick Reference Webpage System

I wanted a way of making an arbitrary quick reference sheet full of keyboard
short cuts and various hacks I either want to commit to memory or only
occasionally use but want handy. In particular, I really want this sheet
to pop up on screen at the touch of a global short cut, and be dismissed as
easily.

Unfortunately no application quite fits the bill in the Linux space, so what
follows is an overcharged gist that delivers this via Markdown, a custom
renderer script to move the heading1 blocks into separate in-page tabs, a
separate browser profile to load it into, some custom window settings, and a
third party KWin script to handle the minimise/un-minimise global shortcut.

Simples!

Needless to say, some assembly is required, and if you're not running KDE,
you'll need your own set of figurative [Allen
keys](https://en.wikipedia.org/wiki/Hex_key).

## 1. Download the renderer and template

That is, this repository. The renderer is a Python script that depends on
[cmarkgfm](https://pypi.org/project/cmarkgfm/) and [Beautiful
Soup](https://beautiful-soup-4.readthedocs.io/en/latest/#), so install those, eg
```
sudo apt-get install python3-cmarkgfm python3-bs4
```

That worked for me on Ubuntu 23.10. Those packages seem to be common and fairly
stable.

## 2. Make some Markdown input

Go scribble some initial notes into some Markdown file of your choosing. I
suggest creating a few level 1 headings to see the tabs in action, and maybe
wrap some keyboard short cuts in double square brackets to see if you like
that resulting mark up, eg:
```
[[Alt]] [[c]] — Comment region
```

## 3. Render some HTML output

It's basically:
```
cd ~/git/quick-reference-webpage/
./render_quick_reference_webpage.py --template ./qrw-template.html ${your_input.md} > ${your_output.html}
```

That'll get you a basic web page you can load up in a browser.

## 4. Make a browser profile to run it in

Look, you *could* just load this up in a separate window of your main browser
session, but you're probably going to want to start it up independently, trim
the browser UI components down to the minimum, and you're also going to want to
avoid the consequences of habitually closing your main browser session with the
window controls rather than quitting from the menu only to discover there is
another window minimised and you've just tossed 100+ open tabs into the bit
bucket.

This author's folly is to your benefit; here's how to roll up a new profile in
Firefox:

1. Start it up from a terminal with `firefox --ProfileManager`
2. Click “Create Profile...”
3. Give it a name, like 'Quick Reference', and click “Finish”
4. Make sure “Use the selected profile without asking at startup” is checked,
   and your default profile is the selected one
5. Click “Exit”
6. Load up your new profile with, eg `firefox -P 'Quick Reference'`

Now you can point the browser at your rendered HTML output via a `file:///` URL.

Settings you'll immediately want to change:

1. In Settings → General, tick “Open previous windows and tabs”
2. Head into Settings → Home, and change “Homepage and new windows” to “Custom
   URLs...” and select “Use Current Page”, which should be the rendered quick
   reference you just opened
3. In More Tools → Customize Toolbar... tick the ”Title Bar” check box in the
   bottom right of the page: you need KWin providing the title bar to manage
   more settings in the next section
4. I drop the bookmarks, but otherwise leave the rest. If you're running full
   screen, you won't see that stuff anyway

## 5. Tune the window settings (in KDE 5)

Now that you have a conventional window title bar, you can right click on it to
select More Actions → Configure Special Window Settings...

The key match setting to select is the window title, which Firefox helpfully
sets to the title of the web page.

1. Click “Add Property...” and select “Window title” from the list
2. Set it to Substring match; the text should be "Quick Reference Webpage — Mozilla Firefox"

What you want to do here is very much down to you. You could specify the window
size and position, though Firefox tends to remember that itself. I prefer to
set the “Virtual Desktop” property to “All Desktops”, “Keep above other
windows” to Yes, and “Minimised” to Yes. Limit them all to “Apply Initially”.

Note: This describes the late KDE 5 special window settings dialog, which is
almost certainly very similar to the same dialog in early KDE 6, but I'm sure
all bets are off in a few years time.

## 6. Make that profile run on start up (in KDE 5)

We'll need to make a new `.desktop` file for our new Firefox profile to make it
possible to start up from the menus, and able to be auto-started on log in.

1. Create `~/.local/share/applications` if it doesn't already exist
2. `cp /usr/share/applications/firefox.desktop
   ~/.local/share/applications/firefox-your-profile.desktop`
3. Edit that file:
  * Change the “Name” to something like 'Firefox Quick Reference' in the main name
  and your particular locale
  * Change each of the “Exec” keywords to add `-P 'Quick Reference'` to them
4. Now you should be able to search in the main application menu and fine both your
   standard Firefox and the new entry
5. In the KDE System Settings, go to Startup and Shutdown → Autostart
6. Click Add... → Add Application, search on Firefox and select the new entry

## 7. Install the "Toggle Terminal" KWin script (in KDE 5)

This is the secret sauce that drives the Minimise/Un-minimise on global shortcut
behaviour. The script is [Toggle
Terminal](https://github.com/DvdGiessen/kwin-toggleterminal) by Daniël van de
Giessen, and while it's goal is to toggle the visibility of a terminal window,
it so happens that the window title and command to start it up are just
configuration options, so we can use it for our needs.

1. Open the KDE Settings application
2. Go to Window Management → KWin Scripts
3. Click “Get New Scripts...” on the bottom right
4. Search for "terminal toggle"; the one you want will be by 'dvdgiessen'
5. Install it
6. Tick the check box next to the new entry in the list to enable it
6. The new entry in your KWin scripts list will have About, Configure... and
   Delete icons: open the configuration dialog
7. In “Window name prefix” set "Quick Reference Webpage"
8. Leave “Launch command” empty; we're auto-starting
9. Click OK
10. Now go to Shortcuts → KWin and find “Toggle Terminal:”
11. Set that to what you like; I favour Ctrl+F1

(*Note*: Changing Terminal Toggle's settings doesn't seem to take without a
"disable, Apply, enable Apply" cycle.)

## 8. Testing and next steps

* Close the browser and start it again to confirm your window settings do the
  right thing
* Test your shortcut to confirm that's working

That's mostly it for set up.

You'll likely end up running the render script fairly often as your reference
sheet changes, so maybe link it into your path, or wire up your editor to
automatically run a rebuild on a save. I opted to use a systemd service and path
unit to trigger rebuilds when I change the Markdown file. It looks like this:

`qrw-render.service`:
```
[Unit]
Description=Quick Reference Webpage render

[Service]
Type=oneshot
ExecStart=/home/jwm/git/quick-reference-webpage/render_quick_reference_webpage.py --template /home/jwm/git/quick-reference-webpage/qrw-template.html /home/jwm/quick-reference-sheet.md
StandardOutput=truncate:/home/jwm/quick-reference-sheet.html
StandardError=journal
```
`qrw-render.service`:
```
[Unit]
Description=Quick Reference Webpage render path based trigger

[Path]
PathModified=/home/jwm/quick-reference-sheet.md

[Install]
WantedBy=paths.target
```

Change the paths to suit, chuck them under `~/.config/systemd/user`, then run
`systemctl --user enable --now qrw-render.service` to start it up.

*Note*: if your markdown somehow breaks the render script, the service will clobber
your html output, unfortunately.

## Other Environments

### Gnome

Gnome's philosophy regarding customisation seem to be strongly bimodal around
two poles:

* Arrogantly opinionated defaults
* Becoming deeply familiar with the underlying APIs and customising it with
  Javascript

Which, given the environment is supposed to be mainstream, leaves 99% of it's
users forced to pull abandonware-on-first-upload plugins out of a plugin
ecosystem that makes NPM look like the iOS App Store.

Still, it *does* have an API so I suppose you can do all the things that KDE can
do. If you figure that out, raise an issue so we can share that with everyone
else forced to live the desktop environment ghetto life.

### Fvwm, tiling window managers, etc

I am both far too 10ply soft to be using a 20th century retro- window manager,
and an unfrozen caveman who is scared and confused by big brain tiling window
managers. But if you know how to make this work in those environments, bring
school to session in the project issues.

### Mac

I assume there exists some beautiful, artisanal piece of software in the Mac world
that, should I bear witness to it, I would fall to my knees and weep tears of joy due to
it's elegance and majesty. If you know of such software, perhaps I can link it
here?

### Windows

Look, these instructions are already vibing with the complexity and horror of
the lifecycle of some especially exuberant parasitic fluke; the additional steps
to make it work in the Windows world make PostIt notes stuck to your monitor
look compelling. Maybe get a monitor with a larger bezel?

## Bugs

* The render script is doing back slash escaping on the Markdown input at some
  particular, or potentially multiple stages and really shouldn't be.
* The template should have a baked in dark mode toggle
