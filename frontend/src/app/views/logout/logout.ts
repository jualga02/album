import { Component, inject, ElementRef, viewChild, AfterViewInit, Input, EventEmitter, Output, ChangeDetectorRef, OnInit } from '@angular/core';
import { Albumcalls } from '../../services/albumcalls';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth-service';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-logout',
  imports: [],
  templateUrl: './logout.html',
  styleUrl: './logout.css',
})
export class Logout implements OnInit, AfterViewInit{
  public data = inject(Albumcalls);
  private router = inject(Router);
  private authService = inject(AuthService);
  private _cdr = inject(ChangeDetectorRef);

  @Output() close = new EventEmitter<boolean>();

  readonly modalElement = viewChild<ElementRef>('bootstrapModal');
  private modalInstance: any;

  public userData: any = null;
  public isLoading: boolean = true;

 

  url:string = `${environment.apiUrl}/users/me/items`;


 

  async ngAfterViewInit() {
    // Inicializamos y abrimos la modal dinámicamente al cargar la ruta
    
      try {
        // Importación dinámica de Bootstrap para evitar errores de SSR
        const bootstrap = await import('bootstrap');
        const element = this.modalElement()?.nativeElement;
      
        if (element) {
          this.modalInstance = new bootstrap.Modal(element, {
            backdrop: 'static', // Evita que se cierre haciendo clic fuera
            keyboard: false     // Evita que se cierre con la tecla ESC
          });
          this.modalInstance.show();
        }
    } catch (error) {
      console.error("Error al cargar Bootstrap", error);
    }
  }

  public closeSession(): void {
    window.sessionStorage.removeItem('token');
    window.sessionStorage.removeItem('user_id');
    this.authService.updateUserLogged(null);
    // Esperar a que el modal se cierre para que Bootstrap limpie la clase del body
    if (this.modalInstance) {
      const element = this.modalElement()?.nativeElement;
      if (element) {
        element.addEventListener('hidden.bs.modal', () => {
          this.router.navigate(['/']);
        }, { once: true });
        this.modalInstance.hide();
        return;
      }
    }
    this.router.navigate(['/']);
  }

  cerrarModal() {
    if (this.modalInstance) {
      const element = this.modalElement()?.nativeElement;

      if (element){
        element.addEventListener('hidden.bs.modal', () => {
          this.router.navigate(['/']);
        }, { once: true });
        
        this.modalInstance.hide();
      } else {
        this.router.navigate(['/']);
      }


    } else {
      this.router.navigate(['/']);
    }
  }
  
  // ¿Borramos esta función?
  onSubmit(event: Event) {
    event.preventDefault();
    // Aquí pondremos la función de edición de usuario.
    console.log('Datos enviados correctamente...');
  }

  // ¿Borramos esta función?
  public ngOnInit() {
    this.data.getUser(this.url).subscribe({
      next: (response) => {
        console.log(response);
        this.userData = response; // Guardamos los datos
        this.isLoading = false;
        this._cdr.markForCheck();
      },
      error: (err) => {
        console.error('Error al cargar el perfil:', err);
        this.isLoading = false;
        this._cdr.markForCheck();
      }
    });        
  }

  /*public modifyProfile(): void {
    //this.cerrarModal(); // Al cambiar de ruta la modal se cerrará automáticamente.
    this.router.navigate(['updateprofile']);
  }*/

  ngOnDestroy() {
    if (this.modalInstance) {
      this.modalInstance.dispose();
    }

    // 🛡️ Limpieza de seguridad: Forzar la restauración del scroll 
    // por si el componente se destruye abruptamente (ej. botón "Atrás" del navegador)
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
    
    // Eliminar cualquier fondo oscuro (backdrop) residual
    const backdrop = document.querySelector('.modal-backdrop');
    if (backdrop) {
      backdrop.remove();
    }
  }
}
