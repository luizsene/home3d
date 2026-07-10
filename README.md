# Home3D

Home3D is a long-term open source platform for 3D visualization and automation workflows on top of Home Assistant.

Sprint 1 establishes a professional Nx workspace foundation with strict architectural boundaries and interface-first modules.

## Overview

- Monorepo powered by Nx + PNPM.
- React 19 + Vite viewer application.
- TypeScript-first module ecosystem.
- Home Assistant custom component preserved as a separated runtime boundary.
- Build pipeline prepared for future HACS publication flow.

## Architecture

- apps/viewer: UI, Three.js rendering, GLB loading, camera controls.
- apps/documentation: documentation app boundary.
- libs/*: domain and technical contracts split by responsibility.
- custom_components/home3d: Home Assistant integration runtime.

Detailed docs:

- docs/architecture.md
- docs/folder-structure.md
- docs/development.md
- docs/coding-guidelines.md
- docs/nx-workspace.md
- docs/build-pipeline.md
- docs/roadmap.md

## Structure

```text
homeassistant-home3d/
	apps/
		viewer/
		documentation/
	libs/
		core/
		sdk/
		common/
		testing/
		ui/
		heatmap/
		renderer/
		state/
		devices/
		cameras/
		automation/
		strategies/
	custom_components/
		home3d/
	blender/
	docs/
	examples/
	scripts/
	tools/
	.github/
	nx.json
	package.json
	pnpm-workspace.yaml
	tsconfig.base.json
	README.md
```

## How to run

1. Install dependencies:

```bash
pnpm install
```

2. Run viewer locally:

```bash
pnpm nx run viewer:serve
```

3. Build viewer:

```bash
pnpm nx run viewer:build
```

4. Generate dependency graph:

```bash
pnpm nx graph
```

## Build and delivery flow

Target pipeline (structure defined in Sprint 1):

1. Nx Build
2. Viewer output in apps/viewer/dist
3. Scripts boundary
4. Copy boundary
5. custom_components/home3d/www

Current copy script entrypoint:

- scripts/copy-homeassistant.ts

## HACS distribution

Source monorepo (development):

- https://github.com/luizsene/casa3d

Distribution repository (HACS runtime only):

- https://github.com/luizsene/home3d

The distribution workflow publishes only the required runtime files:

- hacs.json
- custom_components/home3d
- README.md
- LICENSE

Workflow file:

- .github/workflows/publish-hacs-distribution.yml

Repository configuration required in the source repository:

1. Secret HACS_DISTRIBUTION_TOKEN with write access to https://github.com/luizsene/home3d.
2. Optional variable HACS_DISTRIBUTION_REPO (default is luizsene/home3d).
3. Optional variable HACS_DISTRIBUTION_BRANCH (default is main).

Local command to validate package generation before publishing:

```bash
pnpm run prepare:hacs-dist -- --out .release/hacs-dist
```

Publication triggers:

1. Manual run via workflow_dispatch.
2. Automatic run when a GitHub Release is published.

## Contributing

1. Follow SOLID and Clean Architecture.
2. Keep modules cohesive and decoupled.
3. Add interfaces before concrete implementations.
4. Keep business logic out of presentational components.
5. Validate lint, tests and build before opening PR.

## Roadmap

- Sprint 1: Workspace
- Sprint 2: Panel Registration
- Sprint 3: Frontend Bridge
- Sprint 4: SDK
- Sprint 5: State Store
- Sprint 6: Entity Manager
- Sprint 7: Scene Sync
- Sprint 8: HeatMap
- Sprint 9: Camera Manager
- Sprint 10: Automation Layer
- Sprint 11: Performance
- Sprint 12: Publicacao HACS

## Technologies

- Nx Workspace
- PNPM
- TypeScript
- React 19
- Vite
- Python 3.13
- Home Assistant Custom Components
- ESLint
- Prettier
- Husky
- lint-staged

## License

MIT. See LICENSE.
