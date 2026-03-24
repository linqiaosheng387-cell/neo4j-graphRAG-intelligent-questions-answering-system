import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import QAManagement from '../views/QAManagement.vue'
import GraphManagement from '../views/GraphManagement.vue'
import DataManagement from '../views/DataManagement.vue'
import OperationMonitoring from '../views/OperationMonitoring.vue'
import UserAccessLogs from '../views/UserAccessLogs.vue'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/qa',
    name: 'QAManagement',
    component: QAManagement
  },
  {
    path: '/graphs',
    name: 'GraphManagement',
    component: GraphManagement
  },
  {
    path: '/data',
    name: 'DataManagement',
    component: DataManagement
  },
  {
    path: '/logs',
    name: 'OperationMonitoring',
    component: OperationMonitoring
  },
  {
    path: '/access',
    name: 'UserAccessLogs',
    component: UserAccessLogs
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
