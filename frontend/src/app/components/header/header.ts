import { ChangeDetectorRef, Component, effect, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from '../../services/auth-service';
import { Albumcalls } from '../../services/albumcalls';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-header',
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './header.html',
  styleUrl: './header.css',
})
export class Header {
  private _change = inject(ChangeDetectorRef);
  protected authService = inject(AuthService);
  private data = inject(Albumcalls);

  public showNav:boolean = true;
  usuario: string | null = '';
  public showPanel: boolean = false;
  public urlU:string = `${environment.apiUrl}/admin/get_user/`;

  constructor() {
    // El effect se ejecuta automáticamente cuando cambia el estado de login
    effect(() => {
      const usuarioActual = this.authService.userLogged();
      this.usuario = usuarioActual;
      console.log(`[header] Se ha detectado un cambio de usuario a: ${usuarioActual}`);

      if (usuarioActual) {
        // Solo llamamos al backend si hay un usuario logueado
        this.checkAdminRole(usuarioActual);
      } else {
        // Si no hay usuario (logout), ocultamos el panel inmediatamente
        this.showPanel = false;
      }
      
      this._change.markForCheck();
    });
  }

    private checkAdminRole(username: string): void {
    this.data.getUser(this.urlU + username).subscribe({
      next: (response) => {
        // Verificamos que la respuesta exista y el rol sea admin
        if (response && response.rol === 'admin') {
          this.showPanel = true;
        } else {
          this.showPanel = false;
        }
        this._change.markForCheck();
      },
      error: (err) => {
        // Si da error (ej. 403 Forbidden porque no es admin, o 401), ocultamos el panel
        console.warn('No se pudo verificar el rol de admin:', err);
        this.showPanel = false;
        this._change.markForCheck();
      }
    });
  }

  public onRouteActivated(componentRef: any):void {
    // Opción A: Cambiar la variable CADA VEZ que se navega a cualquier vista
    //this.showNav = false;

    // Opción B: Cambiar la variable solo si el componente hijo cumple una condición
    // o si el hijo tiene una propiedad específica
    if (componentRef && 'showNav' in componentRef) {
      this.showNav = componentRef.showNav;
      
      //console.log('El componente hijo tiene una propiedad:', componentRef.customProperty);
    } else {
      this.showNav = true; //Valor por defecto si  volvemos a otras vistas
    }
    this._change.markForCheck();
  }
}
