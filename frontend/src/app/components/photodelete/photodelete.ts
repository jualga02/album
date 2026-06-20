import { ChangeDetectorRef, Component, inject, Input, OnInit } from '@angular/core';
import { Albumcalls } from '../../services/albumcalls';
import { Photoresponse } from '../../models/photoresponse.interface';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-photodelete',
  imports: [],
  templateUrl: './photodelete.html',
  styleUrl: './photodelete.css',
})
export class Photodelete implements OnInit {
  public data = inject(Albumcalls);
  private _cdr = inject(ChangeDetectorRef);

  @Input() images: Photoresponse[] = [] as Photoresponse[];
  @Input() id: number = 0;

  filename:string = this.images?.[this.id]?.file || '';
  photoTitle:string = this.images?.[this.id]?.title || '';

  urlDel:string = `${environment.apiUrl}/fotos/delete/`;

  // Variables para gestionar los mensajes del formulario
  successMessage: string | null = null;
  errorMessage: string | null = null;

 

  public deletePhoto(url:string):void {


    // Limpiamos alertas previas antes de enviar
    this.successMessage = null;
    this.errorMessage = null;

    this.data.deletePhoto(url).subscribe({
      next: (response: any) => {
        //const fileName = this.file?.name || 'archivo';
        this.successMessage = response?.message || 'El archivo se ha eliminado con éxito';
        this._cdr.markForCheck();
      },
      error: (err: any) => {
        console.error(err);
        this.successMessage = null;
        // Mostramos el detalle real del backend cuando exista; si no, usamos un fallback.
        this.errorMessage = err.error?.detail || err.message || 'Ocurrió un error inesperado al borrar el archivo.';
        this._cdr.markForCheck();
      }
    });
  }

  

  public onSubmit():void {
    const selectedPhoto = this.images?.[this.id];

    if (!selectedPhoto?.file) {
      this.successMessage = null;
      this.errorMessage = 'No se ha encontrado la foto que quieres borrar.';
      this._cdr.markForCheck();
      return;
    }

    this.filename = selectedPhoto.file;
    this.deletePhoto(this.urlDel + encodeURIComponent(this.filename));
     // this.resetForm();
    
  }

  public ngOnInit(): void {
    // Si el componente se inicializa sin inputs, evitamos errores de acceso a propiedades.
    if (this.images?.[this.id]) {
      this.filename = this.images[this.id].file;
      this.photoTitle = this.images[this.id].title;
    } else {
      this.filename = 'desconocida';
    }
  }

  
}
