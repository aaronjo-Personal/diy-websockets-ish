// https://javascript.plainenglish.io/how-to-track-the-users-mouse-s-position-with-javascript-8b99defa8944

export function trackMouse(
  onMove: (position: { readonly x: number; readonly y: number }) => void,
) {
  document.addEventListener("pointermove", (event) => {
    onMove({
      // send positions as fractions to account for diff display ratios
      x: event.clientX / window.innerWidth,
      y: event.clientY / window.innerHeight,
    });
  });
}
