# SKILL: Minimal Surreal Editorial Composition v2

## Intent

Generate restrained documentary-surreal images that hold onto the subject first and let one wrong state or anomaly create the tension.

The goal is not abstract poster minimalism. The goal is a readable subject, reduced just enough, with one controlled contradiction.

---

## Hard Constraints

1. Dominant Read
- The image must have one clear subject or one clear scene state.
- The subject must remain recognizable after simplification.
- Do not let style wipe out what the thing is.

2. Single Anomaly
- Use one dominant anomaly, contradiction, or wrong state.
- Keep the rest of the image coherent.
- Do not stack surreal effects.

3. Controlled Palette
- Keep the palette disciplined and low-noise.
- One accent is allowed but not required.
- Accent can be saturated or simply higher-contrast than the rest of the frame.

4. Stillness
- No motion blur, action framing, or theatrical event depiction.
- The frame should feel held, paused, or officially calm.

5. Clean Output
- No text, logos, UI overlays, or poster graphics.
- No collage fragments unless the job is explicitly collage.
- Thumbnail readability matters more than ornamental detail.

---

## Soft Constraints

- Asymmetry is useful when it improves clarity, but not mandatory.
- Negative space should support readability, not hit a quota.
- Lighting may be soft, flat, or mildly directional as long as it stays restrained.
- Human presence is allowed only when it helps scale or context, and should stay minimal.

---

## Subject Guidance

Prioritize concrete subjects:

- machines
- rooms
- workstations
- vehicles
- structural systems
- evidence-like objects

Valid reads:

- object portrait
- evidence room still
- environmental thesis frame

Avoid:

- crowded symbolic boards
- dream-logic surrealism
- multiple equal focal points
- purely abstract geometry with no subject anchor

---

## Composition Guidance

- Choose the clearest subject placement for the scene.
- Off-center framing is often useful, but center or near-center is allowed if it makes the subject read better.
- Do not force giant empty thirds if they weaken the image.
- Reduction should simplify the frame, not hollow it out.

---

## Color Strategy

- Keep the palette controlled and legible.
- Use neutrals and restrained field colors first.
- Treat the anomaly signal as semantic, not decorative.
- Avoid multiple competing accents and noisy color chatter.

---

## Lighting

- Prefer restrained lighting over dramatic lighting.
- Flat institutional light, soft clinical light, or gentle directional light are all valid.
- Avoid blockbuster contrast and cinematic spectacle.

---

## Output Requirements

- Clear main read at thumbnail size
- One dominant anomaly
- No text or interface artifacts
- Reduced but not empty
- Subject identity still intact

---

## Anti-Patterns

- forced poster emptiness
- dead abstract geometry with no readable subject
- multiple surreal events
- graphic-design overlays baked into the image
- melodramatic lighting
- collage logic when the job calls for documentary surrealism

---

## Prompt Construction Template

1. Concrete subject and scene
2. What must remain recognizable
3. One anomaly or wrong state
4. Palette logic
5. Lighting and restraint clause

Do not encode caption-safe bands or keep-out rectangles into the model prompt.

---

## Example Prompts

Example 1:
"A hospital radiotherapy machine in a quiet treatment room, the device remains clearly recognizable and dominates the frame, one thin red fault seam glows inside the otherwise normal housing, palette of off-white, pale cyan, and charcoal, restrained clinical lighting, still and unspectacular."

Example 2:
"A control console bank in an institutional room, the console geometry remains readable, one duplicated status light appears where only one should exist, muted beige and smoked blue palette, flat official lighting, reduced but not empty."

Example 3:
"A launch vehicle on the pad under cold sky, the stack remains immediately recognizable, one wrong plume state appears at the booster joint while the rest stays physically coherent, restrained gray-blue palette with one ember accent, stillness over drama."

---

## Flux / ComfyUI Notes

- Prefer shorter prompts with concrete nouns.
- Lower abstraction usually gives better consistency than stacking layout theory.
- Keep CFG moderate and do not over-specify composition.
- Concrete scene state beats symbolic art-direction language.

---

## Completion Criteria

An image is valid if:

- the subject reads immediately
- the anomaly reads clearly
- the frame feels restrained
- the style serves the scene instead of replacing it
