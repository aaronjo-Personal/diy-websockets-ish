// https://javascript.plainenglish.io/how-to-track-the-users-mouse-s-position-with-javascript-8b99defa8944
import { Stream } from "effect";

export const mousePositions = Stream.fromEventListener<PointerEvent>(document, "pointermove").pipe(
  Stream.map((event) => ({
    // send positions as fractions to account for diff display ratios
    x: event.clientX / window.innerWidth,
    y: event.clientY / window.innerHeight,
  })),
);
