import { Effect } from "effect";
import type { Participant } from "./websocket";

export const renderMice = Effect.gen(function* () {
  const layer = yield* Effect.acquireRelease(
    Effect.sync(() => {
      const element = document.createElement("div");
      element.className = "mice";
      element.setAttribute("aria-hidden", "true");
      document.body.append(element);
      return element;
    }),
    (element) => Effect.sync(() => element.remove()),
  );
  const mice = new Map<string, HTMLDivElement>();

  return (participants: readonly Participant[], ownId: string) =>
    Effect.sync(() => {
      const others = participants.filter((participant) => participant.id !== ownId);
      const connectedIds = new Set(others.map((participant) => participant.id));

      for (const [id, mouse] of mice) {
        if (!connectedIds.has(id)) {
          mouse.remove();
          mice.delete(id);
        }
      }

      for (const participant of others) {
        let mouse = mice.get(participant.id);
        if (mouse === undefined) {
          mouse = document.createElement("div");
          mouse.className = "mouse";
          mouse.dataset["participantId"] = participant.id;
          layer.append(mouse);
          mice.set(participant.id, mouse);
        }
        mouse.style.left = `${participant.x * 100}%`;
        mouse.style.top = `${participant.y * 100}%`;
      }
    });
});
