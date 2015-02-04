Simple application designed to generate the prompts I use for the bash shell console for my personal systems in my LAN.
Eventually I want this to be highly configurable/customizeable that others will want to potentially use the same mechanism
for their own systems.

The basic premise is I wanted something that could generate a string that can be assigned to the PS1 environment variable,
with all of the various pieces I wanted to use for my prompt stitched together, properly constructing ANSI escape sequences
necessary to colorize the prompt pieces to my liking in a simple way. I don't like to have to remember the ANSI escape codes
to write them by hand, but would rather be able to use things like colors using known names for colors (like Red, Orange,
Goldenrod, etc) or even using known color definition styles (RGB, HSV/HSL, 6x6x6 cube, grayscale, etc) and have it give the
correct ANSI sequence from these codes automatically. Each piece also can rely on extremely quick and efficient code snippets
wrapped corectly within the code to dynamically generate everything for the PS1 prompt through a simple command.
