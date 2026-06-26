import { Component, inject, ElementRef, viewChild, AfterViewInit, OnInit, ChangeDetectorRef } from '@angular/core';
import { Router } from '@angular/router';
import { Albumcalls } from '../../services/albumcalls';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-control-panel',
  imports: [],
  templateUrl: './control-panel.html',
  styleUrl: './control-panel.css',
})
export class ControlPanel implements OnInit, AfterViewInit {
  public data = inject(Albumcalls);
  private router = inject(Router);
  private _cdr = inject(ChangeDetectorRef);
  
  readonly modalElement = viewChild<ElementRef>('bootstrapModal');
  private modalInstance: any;
  
  public disabledUsers: any[] = [];
  public isLoading: boolean = true;
  public urlD:string = `${environment.apiUrl}/admin/disabled_users`;
  public urlE:string = `${environment.apiUrl}/admin/enable_user/`;

  async ngAfterViewInit() {
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

  ngOnInit() {
    this.loadDisabledUsers();
  }

  loadDisabledUsers() {
    this.isLoading = true;
    this.data.getDisabledUsers(this.urlD).subscribe({
      next: (response) => {
        this.disabledUsers = response;
        this.isLoading = false;
        this._cdr.markForCheck();
      },
      error: (err) => {
        console.error('Error al cargar usuarios deshabilitados:', err);
        this.isLoading = false;
        this._cdr.markForCheck();
      }
    });
  }

  enableUser(username: string) {
    if (!confirm(`¿Estás seguro de que deseas habilitar y validar al usuario "${username}"?`)) {
      return;
    }

    this.data.enableUser(this.urlE + username).subscribe({
      next: () => {
        // Eliminamos el usuario de la lista local para una actualización inmediata sin recargar
        this.disabledUsers = this.disabledUsers.filter(u => u.username !== username);
        console.log(`✅ Usuario ${username} habilitado correctamente`);
        this._cdr.markForCheck();
      },
      error: (err) => {
        console.error(`❌ Error al habilitar al usuario ${username}:`, err);
        alert('Error al habilitar el usuario. Revisa la consola o tus permisos de administrador.');
        this._cdr.markForCheck();
      }
    });
  }

  // cerrarModal() {
  //   if (this.modalInstance) {
  //     const element = this.modalElement()?.nativeElement;
  //     if (element) {
  //       element.addEventListener('hidden.bs.modal', () => {
  //         this.router.navigate(['/']);
  //       }, { once: true });
  //       this.modalInstance.hide();
  //     } else {
  //       this.router.navigate(['/']);
  //     }
  //   } else {
  //     this.router.navigate(['/']);
  //   }
  // }
  
  cerrarModal() {
    if (this.modalInstance) {
      const element = this.modalElement()?.nativeElement;
      if (element) {
        element.addEventListener('hidden.bs.modal', () => {
          // 1️⃣ Redirigimos a la raíz y 2️⃣ recargamos la página al completarse
          this.router.navigate(['/']).then(() => {
            window.location.reload();
          });
        }, { once: true });
        
        this.modalInstance.hide();
      } else {
        // Fallback si el elemento del modal no existe
        this.router.navigate(['/']).then(() => {
          window.location.reload();
        });
      }
    } else {
      // Fallback si la instancia de Bootstrap no existe
      this.router.navigate(['/']).then(() => {
        window.location.reload();
      });
    }
  }

  ngOnDestroy() {
    if (this.modalInstance) {
      this.modalInstance.hide(); // Forzar ocultamiento antes de destruir
      this.modalInstance.dispose();
    }
    // Forzar la restauración del scroll por si el componente se destruye abruptamente
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';

    // Eliminar cualquier fondo oscuro (backdrop) residual que Bootstrap haya dejado
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => backdrop.remove());
  }
}
