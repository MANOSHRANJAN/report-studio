Drop images here, named after the slot they fill:

    p01-cover.jpg   p03-opener.png   p04-feature.webp   ...

Any of .jpg .jpeg .png .webp .avif works. Then run, from the project root:

    python3 skills/magazine-report/scripts/slots.py fill reports/.work/<slug>
    python3 skills/magazine-report/scripts/render.py reports/.work/<slug>

See all slots, their sizes and what should go in each:

    python3 skills/magazine-report/scripts/slots.py list reports/.work/<slug>

Have a file with a different name? Assign it:

    python3 skills/magazine-report/scripts/slots.py fill reports/.work/<slug> --assign p01-cover=~/Desktop/photo.jpg
