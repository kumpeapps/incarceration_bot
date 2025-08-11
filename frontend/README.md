# Frontend

This directory contains the React-based web frontend for the incarceration bot.

## Features

- **Inmate Search & View**: Search and view detailed inmate information
- **Monitor Management**: Add, edit, and manage arrest monitors
- **User Management**: User authentication and authorization
- **Dashboard**: Overview of system statistics and recent activity

## Technology Stack

- **Frontend**: React 18 with TypeScript
- **UI Framework**: Material-UI (MUI)
- **State Management**: Redux Toolkit
- **Authentication**: JWT-based
- **Build Tool**: Vite
- **Styling**: Emotion/styled-components

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Setup

```bash
npm install
npm run dev
```

### Docker

```bash
docker build -t incarceration_bot_frontend .
docker run -p 3000:80 incarceration_bot_frontend
```

## Environment Variables

Create a `.env` file in this directory:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=Incarceration Bot Dashboard
```
