import { RenderMode, ServerRoute } from '@angular/ssr';

export const serverRoutes: ServerRoute[] = [
  // Page publique : peut être générée à l'avance au build
  {
    path: 'login',
    renderMode: RenderMode.Prerender,
  },
  // Pages connectées : rendues dans le navigateur, seul endroit où le jeton
  // (localStorage) existe. Pré-rendues sur le serveur, elles redirigeraient vers /login.
  {
    path: '**',
    renderMode: RenderMode.Client,
  },
];
