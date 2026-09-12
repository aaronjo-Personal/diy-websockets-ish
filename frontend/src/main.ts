import "./style.css";
import { Effect, Fiber } from "effect";
import { mousePositions } from "./mousehelper";
import { renderMice } from "./rendermice";
import { connectToPointerServer } from "./websocket";

const heading = document.createElement("h1");
const list = document.createElement("div");

heading.textContent = "Connected pointers";
list.textContent = "Connecting...";
document.body.replaceChildren(heading, list);

const program = Effect.gen(function* () {
  const render = yield* renderMice;
  yield* connectToPointerServer(mousePositions, (participants, ownId) =>
    render(participants, ownId).pipe(
      Effect.andThen(
        Effect.sync(() => {
          const rows = participants.map((participant) => {
            const row = document.createElement("p");
            row.textContent = `${participant.id} {${participant.x.toFixed(3)}, ${participant.y.toFixed(3)}}`;
            return row;
          });
          list.replaceChildren(...rows);
        }),
      ),
    ),
  );
}).pipe(
  Effect.scoped,
  Effect.catch((error) => Effect.logError("Pointer connection stopped", error)),
  Effect.ensuring(Effect.sync(() => list.replaceChildren())),
);

const connection = Effect.runFork(program);
import.meta.hot?.dispose(() => Effect.runFork(Fiber.interrupt(connection)));
