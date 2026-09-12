import { Effect, Schedule, Schema, Stream } from "effect";
import { Socket } from "effect/unstable/socket";

const Coordinate = Schema.Number.check(Schema.isBetween({ minimum: 0, maximum: 1 }));
const Position = Schema.Struct({ x: Coordinate, y: Coordinate });
export type Position = typeof Position.Type;

const Participant = Schema.Struct({ id: Schema.String, ...Position.fields });
export type Participant = typeof Participant.Type;

const decodeMessage = Schema.decodeUnknownEffect(
  Schema.fromJsonString(
    Schema.Union([
      Schema.Struct({ type: Schema.Literal("welcome"), id: Schema.String }),
      Schema.Struct({
        type: Schema.Literal("participants"),
        participants: Schema.Array(Participant),
      }),
    ]),
  ),
);

export const connectToPointerServer = Effect.fn("connectToPointerServer")(
  function* (
    positions: Stream.Stream<Position>,
    onParticipants: (participants: readonly Participant[], ownId: string) => Effect.Effect<void>,
  ) {
    let ownId: string | undefined;
    let latestPosition: Position | undefined;
    yield* Effect.forkScoped(
      positions.pipe(
        Stream.runForEach((position) =>
          Effect.sync(() => {
            latestPosition = position;
          }),
        ),
      ),
    );

    const socket = yield* Socket.makeWebSocket(`ws://${window.location.hostname}:6969`);
    const read = yield* Socket.readerString(socket);
    const writer = yield* socket.writer;

    const receive = Effect.gen(function* () {
      for (const text of yield* read) {
        const message = yield* decodeMessage(text);
        switch (message.type) {
          case "welcome":
            ownId = message.id;
            break;
          case "participants":
            if (ownId !== undefined) {
              yield* onParticipants(message.participants, ownId);
            }
            break;
        }
      }
    }).pipe(Effect.forever);

    const send = Effect.gen(function* () {
      if (latestPosition !== undefined) {
        const position = latestPosition;
        latestPosition = undefined;
        yield* writer.write(JSON.stringify({ type: "pointer", ...position }));
      }
    }).pipe(Effect.repeat(Schedule.spaced("50 millis")));

    yield* Effect.raceFirst(receive, send);
  },
  Effect.scoped,
  Effect.provide(Socket.layerWebSocketConstructorGlobal),
);
