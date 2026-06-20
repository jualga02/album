import { Component, inject, ElementRef, viewChild, AfterViewInit, Input, EventEmitter, Output, ChangeDetectorRef } from '@angular/core';
import { Albumcalls } from '../../services/albumcalls';
import { Router } from '@angular/router';
import { ReactiveFormsModule, FormGroup, FormControl, Validators, AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';
import { AuthService } from '../../services/auth-service';
import { environment } from '../../../environments/environment';

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

@Component({
  selector: 'app-updateprofile',
  imports: [ReactiveFormsModule],
  templateUrl: './updateprofile.html',
  styleUrl: './updateprofile.css',
})
export class Updateprofile {
    public data = inject(Albumcalls);
    private router = inject(Router);
    private authService = inject(AuthService);
    private _cdr = inject(ChangeDetectorRef);
  
    @Output() close = new EventEmitter<boolean>();
  
    readonly modalElement = viewChild<ElementRef>('bootstrapModal');
    private modalInstance: any;
  
    successMessage: string | null = null;
    errorMessage: string | null = null;
  
    form = new FormGroup({
      username: new FormControl(''),
      full_name: new FormControl(''),
      email: new FormControl('', { validators: [Validators.pattern(emailPattern)] }),
    });
  
    url:string = `${environment.apiUrl}/users/update/` + this.authService.userLogged();
    
  
    public patchUser(url:string):void {

      const body: {
        username?: string;
        full_name?: string;
        email?: string; 
      } = {};

      const username = this.form.value.username?.trim();
      const full_name = this.form.value.full_name?.trim();
      const email = this.form.value.email?.trim();

      if (username) body.username = username;
      if (full_name) body.full_name = full_name;
      if (email) body.email = email;

      // Limpiamos alertas previas antes de enviar
      this.successMessage = null;
      this.errorMessage = null;

      this.data.patchUser(url,body).subscribe({
        next: (response:any) => {
          console.log(response);
          this.errorMessage = null;
          this.successMessage = response?.message || '  ';
          this._cdr.markForCheck(); // Asegura que el cambio se refleje en la vista
        },
        error: (err: any) => {
          console.error(err);
          this.successMessage = null;
  
          const backendMessage = err?.error?.detail || err?.error?.message || '';
  
          if (err?.status === 409) {
            this.errorMessage = 'Nombre de usuario o correo ya existen.';
          } else if (err?.status === 400) {
            this.errorMessage = 'Los datos enviados no son correctos. Revisa los campos e inténtalo de nuevo.';
          } else if (backendMessage) {
            this.errorMessage = backendMessage;
          } else {
            this.errorMessage = 'No se ha podido crear la cuenta. Contacta con el administrador.';
          }
          this._cdr.markForCheck(); // Asegura que el cambio se refleje en la vista
        }
        
      });
    }
  
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
  
    cerrarModal() {
      if (this.modalInstance) {
        const element = this.modalElement()?.nativeElement;
  
        if (element){
          element.addEventListener('hidden.bs.modal', () => {
            this.router.navigate(['default']);
          }, { once: true });
          
          this.modalInstance.hide();
        } else {
          this.router.navigate(['default']);
        }
  
  
      } else {
        this.router.navigate(['default']);
      }
    }
    
    onSubmit() {
      if (this.form.valid) {
        this.patchUser(this.url);
        this.resetForm();
        return;
      }
  
      this.errorMessage = null;
      this.successMessage = null;
    }

    private resetForm(): void {
      this.form.reset({
        username: '',
        full_name: '',
        email: ''
      });
    }

    // Recomendado: Limpia la instancia de Bootstrap si el componente se destruye por otra razón
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
