# Home3D for Home Assistant

<p align="center">

Interactive 3D Digital Twin for Home Assistant

Visualize, monitor and control your entire smart home through a real-time 3D environment.

</p>

---

## Overview

Home3D transforms Home Assistant into a real-time digital twin of your home.

Instead of navigating through dashboards full of cards, Home3D allows your entire house to become the user interface.

Every room, device, light, sensor, switch and automation can be represented inside a fully interactive 3D model synchronized with Home Assistant in real time.

This repository contains only the Home Assistant integration distributed through HACS.

The complete development workspace is available at:

https://github.com/luizsene/casa3d

---

## Vision

Home3D is not intended to be "just another dashboard."

The long-term goal is to create a complete visual layer for Home Assistant where your home itself becomes the interface.

Imagine being able to:

• Click a lamp inside the 3D model to turn it on.

• Watch temperature change in each room.

• Visualize power consumption as a heat map.

• Display live camera feeds directly inside the scene.

• Monitor doors, windows and alarms in real time.

• Simulate automations before enabling them.

• Navigate through floors as if walking inside your home.

Home3D aims to become the Digital Twin of your smart home.

---

# Features

## Current

✔ Native Home Assistant Integration

✔ Sidebar Panel

✔ Configuration Flow

✔ GLB Model Support

✔ Interactive 3D Viewer

✔ Entity Binding System

✔ Local Asset Hosting

✔ Home Assistant WebSocket Integration

✔ Room Management

✔ Persistent Binding Storage

---

## Planned

• Heat Maps

• Energy Visualization

• Temperature Overlay

• Humidity Overlay

• Lighting Effects

• Camera Integration

• Automation Visualization

• Device Animations

• AI Assisted Mapping

• Multi-floor Navigation

• VR Support

• Scene Templates

• Floor Planner Import

• Sweet Home 3D Import

---

# Screens

Future releases will include:

- Interactive house visualization

- Device overlays

- Camera integration

- Energy heat maps

- Automation editor

- Multi-floor navigation

---

# Installation

## Install using HACS

1. Open HACS.

2. Integrations.

3. Search for:

```
Home3D
```

4. Install.

5. Restart Home Assistant.

---

## Manual Installation

Copy

```
custom_components/home3d
```

into

```
config/custom_components/
```

Restart Home Assistant.

Then add the integration from:

Settings

↓

Devices & Services

↓

Add Integration

↓

Home3D

---

# First Setup

After installing the integration:

1. Open Home3D from the sidebar.

2. Enable Configuration Mode.

3. Upload your GLB model.

4. Create rooms.

5. Select objects inside the model.

6. Link each object to Home Assistant entities.

7. Save.

The configuration is stored automatically by the integration.

No YAML configuration is required.

---

# Entity Binding

The Entity Binding System is the core of Home3D.

Every object inside the 3D scene can be connected to one or multiple Home Assistant entities.

Examples

Living Room Lamp

↓

light.living_room

Bedroom Temperature

↓

sensor.bedroom_temperature

Garage Door

↓

cover.garage

Bedroom Air Conditioner

↓

climate.bedroom

Energy Consumption

↓

sensor.house_energy

Door Sensor

↓

binary_sensor.front_door

Once linked, the object automatically reflects the current Home Assistant state.

---

# Supported Entity Domains

Current support includes:

- Light

- Switch

- Fan

- Cover

- Sensor

- Binary Sensor

- Climate

- Media Player

- Camera

Additional domains will be added over time.

---

# Configuration Mode

Configuration Mode allows users to build the relationship between the 3D model and Home Assistant.

Current capabilities

• Create rooms

• Rename rooms

• Upload GLB models

• Link entities

• Remove links

• Save configuration

Future versions will also support:

• Drag & Drop editing

• Object properties

• Color customization

• Animations

• Visibility rules

• Device templates

---

# 3D Model Support

Current supported format

✔ GLB

Recommended workflow

Blender

↓

Export GLB

↓

Upload into Home3D

↓

Bind entities

↓

Done

Future versions will support importing models from:

• Sweet Home 3D

• Floor Planner

• SketchUp

• Revit

---

# Home Assistant Integration

The integration uses native Home Assistant APIs.

Current communication layers

• Configuration Flow

• WebSocket API

• Service Calls

• Entity Registry

• Device Registry

• Area Registry

• Event Bus

• Diagnostics

• Static Asset Hosting

Rendering is entirely client-side.

This keeps Home Assistant lightweight while allowing complex 3D scenes.

---

# Architecture

The Home Assistant integration is intentionally lightweight.

Its responsibilities are:

• Register the sidebar panel

• Store configuration

• Provide WebSocket endpoints

• Serve static assets

• Manage entity bindings

• Register services

• Diagnostics

The 3D engine runs completely in the browser.

---

# Performance

Designed to run on:

✔ Home Assistant OS

✔ Home Assistant Container

✔ Home Assistant Supervised

✔ Home Assistant Green

✔ Home Assistant Yellow

✔ Raspberry Pi

Rendering is GPU accelerated using WebGL.

The Home Assistant server only handles synchronization.

---

# Roadmap

## Phase 1

Workspace

Viewer

Home Assistant Integration

Entity Binding

Configuration Mode

---

## Phase 2

Scene Synchronization

Camera Manager

Device Manager

Heat Maps

Energy Overlay

Temperature Overlay

---

## Phase 3

Automation Designer

AI Assistant

Voice Interaction

Digital Twin Simulation

Scene Templates

Multi-floor Navigation

---

## Development

This repository contains only the Home Assistant runtime.

The complete development workspace is available at:

https://github.com/luizsene/casa3d

Development follows:

- SOLID

- Clean Architecture

- Interface-first Design

- Nx Workspace

- TypeScript

- React

---

# Contributing

Contributions are welcome.

Bug reports, feature requests and pull requests should be opened in the development repository.

https://github.com/luizsene/casa3d

---

# License

MIT License

See LICENSE for details.