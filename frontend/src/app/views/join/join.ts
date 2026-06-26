
import { Component, inject, ElementRef, viewChild, AfterViewInit, Input, EventEmitter, Output, ChangeDetectorRef } from '@angular/core';
import { Albumcalls } from '../../services/albumcalls';
import { Router } from '@angular/router';
import { ReactiveFormsModule, FormGroup, FormControl, Validators, AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';
import { AuthService } from '../../services/auth-service';
import { Newuser } from '../../models/newuser.interface';
import { environment } from '../../../environments/environment';

const passwordsMatchValidator: ValidatorFn = (control: AbstractControl): ValidationErrors | null => {
  const password1 = control.get('password_1')?.value;
  const password2 = control.get('password_2')?.value;

  if (!password1 || !password2) {
    return null;
  }

  return password1 === password2 ? null : { passwordsMismatch: true };
};

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

@Component({
  selector: 'app-join',
  imports: [ReactiveFormsModule],
  templateUrl: './join.html',
  styleUrl: './join.css',
})
export class Join {
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
    username: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
    full_name: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
    email: new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.pattern(emailPattern)] }),
    password_1: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
    password_2: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
  }, { validators: [passwordsMatchValidator] });

  url:string = `${environment.apiUrl}/new_user`;
  

  public createUser(url:string, body: Newuser):void {
    this.data.createUser(url,body).subscribe({
        next: (response) => {
          console.log(response);
          this.errorMessage = null;
          this.successMessage = response?.message || 'La cuenta se ha creado correctamente.';
          //window.sessionStorage.setItem('token',response.access_token);
          //window.sessionStorage.setItem('user_id',String(response.user_id));
          //this.authService.updateUserLogged(response.user_logged);
          //this.token = response.access_token;
          setTimeout(() => {
            this.cerrarModal();
          }, 600);
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
      
    })
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
  //   // Redirige a la ruta principal (o la anterior) para destruir este componente
  //   this.router.navigate(['/']); 
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
    // 🗑️ He eliminado la línea `this.router.navigate(['/']);` que tenías al final
    // del método original, porque era un bug: se ejecutaba siempre, inmediatamente,
    // cortando la animación del modal y provocando navegaciones duplicadas.
  }
  
  onSubmit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.errorMessage = null;
    this.successMessage = null;

    const body: Newuser = {
      username: this.form.value.username!,
      full_name: this.form.value.full_name!,
      email: this.form.value.email!,
      password: this.form.value.password_1!,
    };

    this.createUser(this.url, body);
    console.log('Datos enviados correctamente...');
  }
}

