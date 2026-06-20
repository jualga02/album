import { AfterViewInit, Component, ElementRef, inject, OnInit, viewChild, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ReactiveFormsModule, FormGroup, FormControl, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { Albumcalls } from '../../services/albumcalls';
import { CommonModule } from '@angular/common';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-passrecover',
  imports: [ReactiveFormsModule, CommonModule],
  templateUrl: './passrecover.html',
  styleUrl: './passrecover.css',
})
export class Passrecover implements OnInit, AfterViewInit, OnDestroy {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private albumcalls = inject(Albumcalls);

  readonly modalElement = viewChild<ElementRef>('bootstrapModal');
  private modalInstance: any;

  token: string = '';
  errorMessage: string = '';
  successMessage: string = '';
  urlVal: string = `${environment.apiUrl}/token/pass/validate`;

  passForm = new FormGroup({
    newPassword: new FormControl('', [Validators.required, Validators.minLength(6)]),
    confirmPassword: new FormControl('', [Validators.required])
  }, { validators: this.passwordMatchValidator });

  ngOnInit() {
    // Extraer el token de la URL: /passrecover?token=xyz
    this.token = this.route.snapshot.queryParamMap.get('token') || '';
    if (!this.token) {
      this.errorMessage = 'Enlace de recuperación no válido o faltante.';
    }
  }

  // Inicializar y mostrar el modal automáticamente al cargar la ruta
  async ngAfterViewInit() {
    try {
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

  // Validador personalizado para comprobar que las contraseñas coinciden
  passwordMatchValidator(group: AbstractControl): ValidationErrors | null {
    const pass = group.get('newPassword')?.value;
    const confirmPass = group.get('confirmPassword')?.value;
    return pass === confirmPass ? null : { mismatch: true };
  }

  onSubmit() {
    if (this.passForm.invalid || !this.token) {
      return;
    }

    const newPass = this.passForm.get('newPassword')?.value || '';

    this.albumcalls.validatePassword(this.urlVal,this.token, newPass).subscribe({
      next: (response) => {
        this.successMessage = response.message;
        this.errorMessage = '';
        // Redirigir al login después de 3 segundos
        setTimeout(() => {
          this.router.navigate(['/login']);
        }, 3000);
      },
      error: (err) => {
        this.errorMessage = err?.error?.detail || 'El enlace ha expirado o no es válido. Solicita uno nuevo.';
        this.successMessage = '';
      }
    });
  }
  cerrarModal() {
    if (this.modalInstance) {
      const element = this.modalElement()?.nativeElement;
      if (element) {
        element.addEventListener('hidden.bs.modal', () => {
          this.router.navigate(['/login']);
        }, { once: true });
        this.modalInstance.hide();
      } else {
        this.router.navigate(['/login']);
      }
    } else {
      this.router.navigate(['/login']);
    }
  }

  // =========================================================================
  // SOLUCIÓN AL FONDO OPACO RESIDUAL (BACKDROP HUÉRFANO)
  // =========================================================================
  ngOnDestroy() {
    if (this.modalInstance) {
      this.modalInstance.hide();    // Forzar ocultamiento antes de destruir
      this.modalInstance.dispose(); // Liberar recursos de Bootstrap
    }
    
    // 1. Forzar la restauración del scroll del body
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
    
    // 2. Eliminar manualmente cualquier fondo oscuro (.modal-backdrop) residual
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => backdrop.remove());
  }
}
