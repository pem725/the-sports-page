# Fonts — build inputs for the brand art

`build_merch.py` converts type to outlines, so the printer never needs these.
But **the build itself cannot run without them**, and until now they lived only
in a session scratchpad — which meant the logo could not be regenerated on any
machine, including the one that made it. They are committed here so the mark
stays reproducible.

| File | Family | Axis used |
|---|---|---|
| `Playfair-var.ttf` | Playfair Display (variable) | `wght` 400–900 |
| `RobotoMono-var.ttf` | Roboto Mono (variable) | `wght` 400–700 |

Both are the same families the website loads from Google Fonts, so the apparel
and the site are set in the same type.

**Licence:** both are released under the SIL Open Font License 1.1, which permits
redistribution — including bundled in a repository like this — provided they are
not sold on their own. Full text: <https://openfontlicense.org/>

Do not subset or re-save these. `instantiateVariableFont` needs the variable
axes intact.
