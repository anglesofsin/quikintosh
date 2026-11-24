// One policy for banners, island notifications and manual sound previews.
function permitted(state) {
    return !state.replayed && !state.dnd && !state.suppress && state.volume > 0 &&
        (state.preview || (state.enabled && state.allowed && state.appSound));
}
if (typeof module !== 'undefined') module.exports = {permitted};
