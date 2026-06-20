import { ChangeDetectorRef, Component, ElementRef, inject, ViewChild, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Albumcalls } from '../../services/albumcalls';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [ReactiveFormsModule, CommonModule],
  templateUrl: './upload.html',
  styleUrls: ['./upload.css'],
})
export class Upload {
  public data = inject(Albumcalls);
  private _cdr = inject(ChangeDetectorRef);

  url:string = `${environment.apiUrl}/new_foto/`;
  file: File = {} as File;

  // Comunicación con el componente padre
  onClose = output<void>();

  // Variables para gestionar los mensajes del formulario
  successMessage: string | null = null;
  errorMessage: string | null = null;

  form = new FormGroup({
    shot_date: new FormControl(''),
    comment: new FormControl(''),
    tag: new FormControl(''),
    title: new FormControl(''),
    video: new FormControl(false)
  })

  @ViewChild('fileInput') fileInput!: ElementRef<HTMLInputElement>;

  public createPhoto(url:string):void {
    const userId = window.sessionStorage.getItem('user_id') || '';
    const body = new FormData();
    // Añadimos los campos equivalentes a los modificadores -F de curl
    body.append('shot_date', this.form.value.shot_date ?? '');
    body.append('comment', this.form.value.comment ?? '');
    body.append('tag', this.form.value.tag ?? '');
    body.append('file', this.file);               //, this.file.name);
    body.append('title', this.form.value.title ?? '');
    body.append('video', String(!!this.form.value.video!));
    body.append('user_id', userId);

    // Limpiamos alertas previas antes de enviar
    this.successMessage = null;
    this.errorMessage = null;

    this.data.createPhoto(url,body).subscribe({
      next: (response: any) => {
        const fileName = this.file?.name || 'archivo';
        this.successMessage = response?.message || 'El archivo se ha guardado correctamente';
        // Desatascamos la detección de cambios retrasando el reset 100ms
        setTimeout(() => {
          this.resetForm();
        }, 100);
        this._cdr.markForCheck();
      },
      error: (err: any) => {
        console.error(err);
        this.successMessage = null;
        // Si el backend lanza un HTTPException, el mensaje estará en err.error.detail
        if (err.status === 409) {
          this.errorMessage = err.error?.detail || 'El archivo ya existe en la base de datos.';
        } else {
          this.errorMessage = 'Ocurrió un error inesperado al subir el archivo.';
        }
        this._cdr.markForCheck();
      }
    });
  }

  public onSubmit():void {
    if(this.form.valid){
      this.createPhoto(this.url);
    }
  }

  // Factorizamos la lógica de limpieza en un método independiente
  private resetForm(): void {
    this.form.reset({
      shot_date: '',
      comment: '',
      tag: '',
      title: '',
      video: false
    });
    if (this.fileInput) {
      this.fileInput.nativeElement.value = '';
    }
    this.file = {} as File;
  }

  public onFileSelect(event: any):void {
    if(event.target.files.length > 0) {
      this.file = event.target.files[0];
    }
  }

  public cerrarModal(): void {
    this.form.reset();
    this.onClose.emit();
  }
}
