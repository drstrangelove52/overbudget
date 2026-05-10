import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import AccountsView from '../views/AccountsView.vue'
import TransactionsView from '../views/TransactionsView.vue'
import ImportView from '../views/ImportView.vue'
import RulesView from '../views/RulesView.vue'
import BudgetView from '../views/BudgetView.vue'
import LoginView from '../views/LoginView.vue'
import EinstellungenView from '../views/EinstellungenView.vue'
import InfoView from '../views/InfoView.vue'
import KontenblattView from '../views/KontenblattView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/login', component: LoginView },
    { path: '/', component: HomeView },
    { path: '/konten', component: AccountsView },
    { path: '/konten/:id', component: KontenblattView },
    { path: '/buchungen', component: TransactionsView },
    { path: '/import', component: ImportView },
    { path: '/regeln', component: RulesView },
    { path: '/budgets', component: BudgetView },
    { path: '/einstellungen', component: EinstellungenView },
    { path: '/info', component: InfoView },
  ],
})

router.beforeEach((to) => {
  const loggedIn = !!localStorage.getItem('token')
  if (to.path !== '/login' && !loggedIn) return '/login'
  if (to.path === '/login' && loggedIn) return '/'
})

export default router
