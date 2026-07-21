<!-- File: /docs/setup-guide.md -->

# Development Setup Guide

This document explains how to install and run the STS Capstone Project.

## Required Software

- Git
- Node.js
- npm
- Python
- Visual Studio Code

## Frontend Requirements

The frontend requires:

- Node.js 20.9 or newer
- npm
- A supported web browser

The versions used during the initial setup were:

```text
Node.js: v22.15.0
npm: 11.16.0
Next.js: 16.2.10

## Mantine Design-System Packages

The frontend uses Mantine as its primary component library.

Installed packages include:

```text
@mantine/core
@mantine/hooks
@mantine/form
@mantine/notifications
@mantine/modals
@mantine/dropzone
@mantine/dates
@mantine/charts
@mantine/spotlight
@tabler/icons-react
motion
dayjs
recharts
```

The Mantine configuration is stored in:

```text
frontend/
├── app/
│   └── providers.tsx
├── theme/
│   ├── colors.ts
│   ├── components.ts
│   └── theme.ts
└── postcss.config.cjs
```

### Provider connection

```text
app/layout.tsx
    ↓
app/providers.tsx
    ├── MantineProvider
    ├── ModalsProvider
    └── Notifications
```

Only one global `Notifications` component should be rendered.

## Testing the Mantine Foundation

Run:

```powershell
cd frontend
npm run lint
npm run build
npm run dev
```

Open:

```text
http://localhost:3000
```

Test:

1. Purple theme and cards display.
2. Notification appears.
3. Confirmation modal opens.
4. Confirming the modal produces another notification.
5. Mobile layout stacks the cards and buttons.
6. Browser console has no red errors.