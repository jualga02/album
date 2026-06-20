import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';


export const authGuard: CanActivateFn = (route, state) => {
  const router = inject(Router);
  const token = sessionStorage.getItem('token');

  if (token) {
    return true; // Permet l'accés a la ruta
  }

  // Si no hi ha token, redirigeix al login
  router.navigate(['/login']);
  return false;
};