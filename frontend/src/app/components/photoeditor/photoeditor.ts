import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, inject, Input, OnInit } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { Albumcalls } from '../../services/albumcalls';
import { Photoresponse } from '../../models/photoresponse.interface';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-photoeditor',
  imports: [ReactiveFormsModule, CommonModule],
  templateUrl: './photoeditor.html',
  styleUrl: './photoeditor.css',
})
export class Photoeditor implements OnInit {
  
  public data = inject(Albumcalls);
  private _cdr = inject(ChangeDetectorRef);

  @Input() images: Photoresponse[] = [] as Photoresponse[];
  @Input() id: number = 0;

  filename:string = '';
  photoTitle:string = this.images?.[this.id]?.title || '';

  urlPatch:string = `${environment.apiUrl}/fotos/update/`;

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

  public patchPhoto(url:string):void {

    this.filename = this.images[this.id].file;

    const body: {
      shot_date?: string;
      comment?: string;
      tag?: string;
      title?: string;
      video?: boolean;
    } = {};

    const shotDate = this.form.value.shot_date?.trim();
    const comment = this.form.value.comment?.trim();
    const tag = this.form.value.tag?.trim();
    const title = this.form.value.title?.trim();

    if (shotDate) body.shot_date = shotDate;
    if (comment) body.comment = comment;
    if (tag) body.tag = tag;
    if (title) body.title = title;
    if (this.form.controls.video.dirty) {
      body.video = !!this.form.value.video;
    }

    // Limpiamos alertas previas antes de enviar
    this.successMessage = null;
    this.errorMessage = null;

    this.data.patchPhoto(url,body).subscribe({
      next: (response: any) => {
        //const fileName = this.file?.name || 'archivo';
        this.successMessage = response?.message || 'El archivo se ha modificado con éxito';
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
          this.errorMessage = err.error?.detail || 'La modificación creará conflictos en la base de datos.';
        } else {
          this.errorMessage = 'Ocurrió un error inesperado al modificar el archivo.';
        }
        this._cdr.markForCheck();
      }
    });
  }

  

  public onSubmit():void {
    if(this.form.valid){
      this.filename = this.images[this.id].file;
      this.patchPhoto(this.urlPatch + encodeURIComponent(this.filename));
      this.resetForm();
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
  }

  public ngOnInit(): void {
    // Inicializamos el título de la foto al cargar el componente
    this.photoTitle = this.images?.[this.id]?.title || '';
  }
}
