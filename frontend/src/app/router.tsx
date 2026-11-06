import type { ComponentType } from 'react'
import { createBrowserRouter } from 'react-router'
import LoginPage from '../auth/LoginPage'
import { Loading } from '../components'
import AppShell from './AppShell'
import { NotFound, RouteError } from './RouteError'

// Cada vista se descarga al visitarla: los visores de PDF y EPUB pesan mucho
const page = (load: () => Promise<{ default: ComponentType }>) => async () => ({ Component: (await load()).default })

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    element: <AppShell />,
    hydrateFallbackElement: <Loading />,
    children: [
      {
        errorElement: <RouteError />,
        children: [
          { index: true, lazy: page(() => import('../features/dashboard/DashboardPage')) },
          { path: 'readings', lazy: page(() => import('../features/readings/ReadingsPage')) },
          { path: 'readings/:id', lazy: page(() => import('../features/readings/ReaderPage')) },
          { path: 'quizzes', lazy: page(() => import('../features/quizzes/QuizzesPage')) },
          { path: 'quizzes/:id', lazy: page(() => import('../features/quizzes/QuizPage')) },
          { path: 'labs', lazy: page(() => import('../features/labs/LabsPage')) },
          { path: 'labs/:id', lazy: page(() => import('../features/labs/LabPage')) },
          { path: 'roadmap/:id?', lazy: page(() => import('../features/roadmap/RoadmapPage')) },
          { path: 'paths', lazy: page(() => import('../features/paths/PathsPage')) },
          { path: 'paths/:id', lazy: page(() => import('../features/paths/PathPage')) },
          { path: 'assistant/:id?', lazy: page(() => import('../features/assistant/AssistantPage')) },
          { path: '*', element: <NotFound /> },
        ],
      },
    ],
  },
])
