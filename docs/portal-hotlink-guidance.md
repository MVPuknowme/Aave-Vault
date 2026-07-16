# Aura Core Portal Touch Hotlink Support

The Aura Core portal currently prevents hot links from opening when tapped on touch devices. This guide outlines a safe way to re-enable link activation without affecting the existing desktop click behavior.

## Problem summary

Many of the portal cards and menu items wrap anchors inside elements that capture the touch event (e.g., for drag or scroll gestures) and stop propagation. As a result, tapping the anchor never triggers navigation even though the link works with a mouse click.

## Recommended fix

1. Ensure the anchor is the topmost interactive element so it receives the touch event:

   ```css
   /* Prevent parent containers from blocking taps */
   .touch-hotlink {
     pointer-events: auto;
     touch-action: manipulation;
   }

   /* Avoid invisible overlays blocking the anchor */
   .touch-hotlink-overlay {
     pointer-events: none;
   }
   ```

2. Add a light-touch handler that mirrors the click navigation for touch users without changing desktop behavior:

   ```javascript
   const hotlinks = document.querySelectorAll('[data-touch-hotlink]');

   hotlinks.forEach((link) => {
     link.addEventListener(
       'touchend',
       (event) => {
         const target = event.currentTarget;
         if (target instanceof HTMLAnchorElement && target.href) {
           // Use the anchor's target to honor new-tab behavior when present
           window.open(target.href, target.target || '_self');
         }
       },
       { passive: true }
     );
   });
   ```

3. Avoid `event.preventDefault()` or `stopPropagation()` on parent wrappers unless necessary, and when they are required, re-dispatch the touch event to the anchor so it can open the link.

## Rollout checklist

- [ ] Apply the `.touch-hotlink` class to anchors that should open on tap.
- [ ] Remove or disable overlay elements with `pointer-events: none` so they do not block the anchor.
- [ ] Verify both tap and mouse click behaviors on iOS and Android.
- [ ] Keep the handler passive to avoid scroll performance regressions.
