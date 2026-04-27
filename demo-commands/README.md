# Demo Commands (Windows)

Double-click any `.cmd` file in this folder to run a grouped demo flow.

## Before you run

- Start your server first.
- For Part 1 (single node), run your app on `http://localhost:7000`.
- For Part 2 (router), run the router on `http://localhost:7000` and nodes on their configured ports.

## Files

- `01-part1-basic.cmd` - PUT, GET, PATCH basic API flow
- `02-part1-version-and-errors.cmd` - ifVersion success/conflict + missing key
- `03-part2-router-flow.cmd` - multi-node PUT/GET + key listing from router
- `04-part1-concurrency-hint.cmd` - runs required 3-client concurrency proof script

Each script ends with `pause` so the terminal stays open during your demo.
