# Titanic ImageGen Full-Pair Deck-Light Repair Provenance

Status: `attempt_01_activated_after_registration_qa`

Attempt 01 was generated as a full-scene ON/OFF pair from the visible Candidate E reference, normalized to 1920x1080, then activated only after lamp-region registration QA passed. The active player still uses the lights-off plate as base and reveals the lights-on plate only through per-light masks. Final render, upload prep, YouTube action, and public release remain blocked.

## Lights On Prompt

```text
Use case: historical-scene
Asset type: Cascade Effects long-form Living Cover backplate, Titanic rough review, lights-on candidate pair 01
Input image role: the visible Candidate E Titanic boat-deck image in the conversation is the composition and style reference.
Primary request: Generate a full-frame 16:9 1920x1080 photorealistic historical scene matching the reference composition as closely as possible: RMS Titanic-style boat deck at dawn, lifeboats under canvas along the left half, davits and rigging repeating into depth, wet wooden deck, ocean and dawn weather on the right, right-rail-safe open sky/sea area for later text, restrained documentary color, layered depth, implied crew/passenger attention.
Lighting state: deck practical lamps are visibly ON. Warm lamp bulbs and tight halos are integrated into nearby metal, canvas, white hull surfaces, and wet deck reflections. The bulbs should be clear source points, not broad bands or full-frame glow.
Composition lock: keep the same camera angle, lifeboat scale, davit rhythm, rail line, horizon, ocean/right-side negative space, and human placement as the reference. No new foreground anchor, no foreground paperwork, no admin props, no text, no signage, no logos, no recognizable faces.
Style constraints: non-Paper-Architecture, cinematic photoreal documentary backplate, historically anchored but not archival, no illustration look, no poster text, no graphic overlays, no diagnostic markers.
Output: landscape 16:9, 1920x1080, no border.
```

## Lights Off Prompt

```text
Use case: historical-scene
Asset type: Cascade Effects long-form Living Cover backplate, Titanic rough review, lights-off candidate pair 01
Input image role: the visible Candidate E Titanic boat-deck image in the conversation is the composition and style reference.
Primary request: Generate a full-frame 16:9 1920x1080 photorealistic historical scene matching the reference composition as closely as possible: RMS Titanic-style boat deck at dawn, lifeboats under canvas along the left half, davits and rigging repeating into depth, wet wooden deck, ocean and dawn weather on the right, right-rail-safe open sky/sea area for later text, restrained documentary color, layered depth, implied crew/passenger attention.
Lighting state: deck practical lamps are OFF/extinguished. No glowing bulbs, no warm halos from the lamps, no strong lamp reflections. Keep only residual dawn/weather light, cool ambient sky light, wet deck reflections, and very faint non-source warmth from the ship interior. The lamp fixtures must remain physically present in the same positions.
Composition lock: keep the same camera angle, lifeboat scale, davit rhythm, rail line, horizon, ocean/right-side negative space, and human placement as the reference. No new foreground anchor, no foreground paperwork, no admin props, no text, no signage, no logos, no recognizable faces.
Style constraints: non-Paper-Architecture, cinematic photoreal documentary backplate, historically anchored but not archival, no illustration look, no poster text, no graphic overlays, no diagnostic markers.
Output: landscape 16:9, 1920x1080, no border.
```
