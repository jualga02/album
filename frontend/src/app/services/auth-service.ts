import { computed, Injectable, signal } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  // 1. Signal privat que conté el valor actual de la sessió
  private userLoggedSignal = signal<string | null>(sessionStorage.getItem('user_logged'));

  // 2. Signal públic de només lectura per als components
  public userLogged = computed(() => this.userLoggedSignal());

  // 3. MÈTODE CRUCIAL: Totes les rutes han d'usar esto per canviar el valor
  public updateUserLogged(newValue: string | null): void {
    if (newValue) {
      sessionStorage.setItem('user_logged', newValue);
    } else {
      sessionStorage.removeItem('user_logged');
    }
    
    // Això notifica instantàniament a qualsevol component de qualsevol ruta
    this.userLoggedSignal.set(newValue);
  }
}

