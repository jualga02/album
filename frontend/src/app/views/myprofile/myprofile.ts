import { Component, inject, ElementRef, viewChild, AfterViewInit, Input, EventEmitter, Output, ChangeDetectorRef, OnInit } from '@angular/core';
import { Albumcalls } from '../../services/albumcalls';
import { Router } from '@angular/router';
import { ReactiveFormsModule, FormGroup, FormControl } from '@angular/forms';
import { AuthService } from '../../services/auth-service';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-myprofile',
  imports: [ReactiveFormsModule],
  templateUrl: './myprofile.html',
  styleUrl: './myprofile.css',
})
export class Myprofile implements OnInit, AfterViewInit {
  public data = inject(Albumcalls);
  private router = inject(Router);
  private authService = inject(AuthService);
  private _cdr = inject(ChangeDetectorRef);

  @Output() close = new EventEmitter<boolean>();

  readonly modalElement = viewChild<ElementRef>('bootstrapModal');
  private modalInstance: any;

  public userData: any = null;
  public isLoading: boolean = true;

  //¿Borramos este formulario.?
  loginForm = new FormGroup({
  })

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

  // cerrarModal() {
  //   if (this.modalInstance) {
  //     const element = this.modalElement()?.nativeElement;

  //     if (element){
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

  // ¿Borramos esta función?
  onSubmit(event: Event) {
    event.preventDefault();
    // Aquí pondremos la función de edición de usuario.
    console.log('Datos enviados correctamente...');
  }

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

  public modifyProfile(): void {
    // 1. Cerrar el modal y esperar a que termine la animación antes de navegar
    if (this.modalInstance) {
      const element = this.modalElement()?.nativeElement;
      if (element) {
        element.addEventListener('hidden.bs.modal', () => {
          this.router.navigate(['updateprofile']);
        }, { once: true });
        
        this.modalInstance.hide();
        return;
      }
    }
    //this.cerrarModal(); // Al cambiar de ruta la modal se cerrará automáticamente.
    this.router.navigate(['updateprofile']);
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
