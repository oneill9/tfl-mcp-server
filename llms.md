# TfL MCP Server

> TfL MCP Server is a community Model Context Protocol server for querying Transport for London data from an AI client.

The [documentation website](https://oneill9.github.io/tfl-mcp-server/) explains how to run the server. It is not a public MCP endpoint and does not provide live results itself. The project is not affiliated with, endorsed by or connected to Transport for London.

## Install and connect

Version 2 uses Node.js 22 or later. An MCP client can launch the npm package over stdio with:

```sh
npx -y @oneill9/tfl-mcp-server@2.0.0
```

The [installation guide](https://oneill9.github.io/tfl-mcp-server/installation/) also covers the `tfl-mcp-server.mcpb` bundle for Claude Desktop and the container image `ghcr.io/oneill9/tfl-mcp-server:2.0.0`.

To build from the [source repository](https://github.com/oneill9/tfl-mcp-server), run:

```sh
cd node
npm ci
npm run build
node dist/index.js
```

The default transport is stdio. From the same `node` directory, start a local HTTP server with:

```sh
HOST=127.0.0.1 PORT=8080 node dist/index.js --http
```

Connect the client to `http://127.0.0.1:8080/mcp`. HTTP uses the MCP 2026-07-28 transport. The stdio server also accepts 2025-era initialization for desktop clients. The old Java, Gradle, Jetty and HTTP SSE implementation is retired. See the [v2 migration guide](https://oneill9.github.io/tfl-mcp-server/migration-v2/).

## Available tools

All six tools query data without modifying TfL services. These are the inputs registered by the [current tool implementation](https://github.com/oneill9/tfl-mcp-server/blob/main/node/src/index.ts).

| Tool | Inputs | Result |
| --- | --- | --- |
| `service_status` | Required `modes`, currently only `"tube"` | Tube line service status. MCP App clients can also show a status board. |
| `arrivals` | Required `stopName` | Arrival predictions after resolving a stop name to its NaPTAN identifier. |
| `journey` | Required `from` and `to` | Journey options between NaPTAN identifiers, postcodes or latitude/longitude pairs. |
| `bike_points` | Optional `query` | Santander Cycles docking stations, with an optional name search. |
| `crowding` | Required `stopName` | Crowding information for a resolved stop. |
| `fares` | Required `fromName` and `toName` | Fare information between named stops. |

The service-status tool currently supports Tube only. Do not assume it accepts bus, rail or other mode names. Data coverage and availability depend on the TfL API. Examples in the documentation are illustrations, not current arrivals, disruption reports or fare quotes.

## Credentials and HTTP access

`TFL_APP_KEY` is optional but recommended for TfL API access and rate limits. `TFL_APP_ID` is optional for older registrations. The [API key guide](https://oneill9.github.io/tfl-mcp-server/api-keys/) explains how to obtain and configure credentials through the TfL developer portal. Keep keys in environment variables or the client's secret configuration.

The HTTP server does not provide OAuth or application authentication. Keep it local, or place it behind a trusted access layer before exposing it to other users. Non-local hostnames also need the `MCP_ALLOWED_HOSTS` allowlist described in the installation guide.

## Sources

- [TfL Unified API](https://api.tfl.gov.uk/) supplies the transport data. Check live tool results when answering questions about current services.
- [README](https://raw.githubusercontent.com/oneill9/tfl-mcp-server/main/README.md) documents the server's current setup.
- [Source repository](https://github.com/oneill9/tfl-mcp-server) contains the tool schemas, implementation and tests.
- [Short reference index](https://oneill9.github.io/tfl-mcp-server/llms.txt) lists the main entry points.
