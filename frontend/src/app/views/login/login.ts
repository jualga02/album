import { Component, inject, ElementRef, viewChild, AfterViewInit, Input, EventEmitter, Output, ChangeDetectorRef } from '@angular/core';
import { Albumcalls } from '../../services/albumcalls';
import { HttpParams } from '@angular/common/http';
import { Router } from '@angular/router';
import { ReactiveFormsModule, FormGroup, FormControl, FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth-service';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, FormsModule],
  standalone: true,
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login implements AfterViewInit{
  public data = inject(Albumcalls);
  private router = inject(Router);
  private authService = inject(AuthService);
  private _cdr = inject(ChangeDetectorRef);

  @Output() close = new EventEmitter<boolean>();

  showRecover: boolean = false;
  recoverEmailControl= new FormControl('', {nonNullable: true});
  recoverMessage: string = '';
  recoverError: string = '';
  isSending: boolean = false;

  readonly modalElement = viewChild<ElementRef>('bootstrapModal');
  private modalInstance: any;

  loginForm = new FormGroup({
    email: new FormControl('', {nonNullable: true}),
    password: new FormControl('', {nonNullable: true})
  })

  urlT:string = `${environment.apiUrl}/token`;
  urlP:string = `${environment.apiUrl}/fotos/1`;
  urlRec:string = `${environment.apiUrl}/token/pass/recover/`;

  token:string = "";
  user:string = "";
  errorMessage: string | null = null;



  public getToken(url:string, bodyParams: HttpParams):void {
    this.data.getToken(url,bodyParams).subscribe((response) => {
      console.log(response);
      window.sessionStorage.setItem('token',response.access_token);
      window.sessionStorage.setItem('user_id',String(response.user_id));
      this.authService.updateUserLogged(response.user_logged);
      this.errorMessage = null;
      this.cerrarModal();
      //this.token = response.access_token;
    }, (err: any) => {
      console.error(err);
      this.errorMessage = err?.error?.detail || err?.error?.message || 'No se pudo iniciar sesión. Revisa tus credenciales e inténtalo de nuevo.';
      this._cdr.markForCheck(); // Asegura que el cambio se refleje en la vista
    });
  }

 
  public getPhoto(url:string):void {
    this.data.getPhoto(url).subscribe((response) => {
      console.log(response);
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
    // Redirige a la ruta principal (o la anterior) para destruir este componente
    this.router.navigate(['/']); 
  }
  
  onSubmit(event: Event) {
    event.preventDefault();
    this.errorMessage = null;

    const bodyParams = new HttpParams()
      .set('username', this.loginForm.value.email || '')
      .set('password', this.loginForm.value.password || '');

    this.getToken(this.urlT, bodyParams);
    console.log('Datos enviados correctamente...');
  }

  toggleRecoverView() {
    this.showRecover = !this.showRecover;
    this.recoverMessage = '';
    this.recoverError = '';
    this.isSending = false;
    this.recoverEmailControl.reset();
  }

  sendRecoverEmail() {
    const email = this.recoverEmailControl.value;
    
    if (!email) {
      this.recoverError = 'Por favor, introduce un correo electrónico.';
      return;
    }

    // 1. Activar estado de carga y limpiar mensajes previos
    this.isSending = true;
    this.recoverError = '';
    this.recoverMessage = '';


    // 3. Petición al backend
    this.data.recoverPassword(this.urlRec, email).subscribe({
      next: (response) => {
       // clearTimeout(timeoutId); // Cancelamos el temporizador si responde antes de 5s
        this.isSending = false;
        this.recoverMessage = 'Si es tu correo, recibirás un enlace (revisa tu spam).';
        this._cdr.markForCheck(); // Asegura que el cambio se refleje en la vista
      },
      error: (err) => {
        // clearTimeout(timeoutId); // Cancelamos el temporizador si hay error antes de 5s
        this.isSending = false;
        this.recoverError = 'Ocurrió un error al procesar la solicitud. Por favor, inténtalo de nuevo.';
        console.error('Error en recuperación de contraseña:', err);
        this._cdr.markForCheck(); // Asegura que el cambio se refleje en la vista
      }
    });
  }
}

