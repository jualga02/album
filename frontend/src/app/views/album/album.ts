import { ChangeDetectorRef, Component, inject, viewChild, OnInit, signal } from '@angular/core';
import { Albumcalls } from '../../services/albumcalls';
import { Photoresponse } from '../../models/photoresponse.interface';
import { Card } from "../../components/card/card";
import { Photoviewer } from '../../components/photoviewer/photoviewer';
import { Userresponse } from '../../models/userresponse.interface';
import { Upload } from '../../components/upload/upload';
import { ReactiveFormsModule, FormGroup, FormControl } from '@angular/forms';
import { Photoeditor } from '../../components/photoeditor/photoeditor';
import { Photodelete } from "../../components/photodelete/photodelete";
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-album',
  imports: [Card, Photoviewer, Photoeditor, Upload, ReactiveFormsModule, Photodelete],
  templateUrl: './album.html',
  styleUrl: './album.css',
})
export class Album implements OnInit{

  private data = inject(Albumcalls);
  private _change = inject(ChangeDetectorRef);
  readonly viewerChild = viewChild(Photoviewer);

  // URLs base (sin query params de paginación)
  private readonly apiUrl = environment.apiUrl;
  private readonly urlUsers   = `${this.apiUrl}/users/all`;
  private readonly urlAll     = `${this.apiUrl}/fotos/all`;
  private readonly urlMulti   = `${this.apiUrl}/fotos/only/`;
  private readonly urlByTitle = `${this.apiUrl}/fotos/search_title/`;
  private readonly urlByTag   = `${this.apiUrl}/fotos/search_tag/`;

  user_logged: string = sessionStorage.getItem("user_logged")!;

  // ========== ESTADO DE PAGINACIÓN ==========
  readonly ITEMS_PER_PAGE = 12;
  currentPage = 0;                    // página actual (0-indexed)
  hasNextPage = signal<boolean>(false);
  hasPrevPage = signal<boolean>(false);
  totalInPage = signal<number>(0);

  // Última URL base usada (para poder recargar al cambiar de página)
  private lastUrlBase = '';
  private lastSearchLabel = '';

  // ========== ESTADO DE LA VISTA ==========
  photoId = 0;
  myPhotos: Photoresponse[] = [];
  photoUsers: Userresponse[] = [];
  seePhotos = false;
  seeModalViewer = false;
  seeModalEditor = false;
  seeModalDelete = false;
  isDropdownOpen = false;
  showUpload = false;
  mostrarConsideraciones = false;
  currentSearch = signal<string>('');

  form = new FormGroup({
    searchBy: new FormControl<'title' | 'tag'>('title'),
    search: new FormControl('')
  });

  // ========== MÉTODO GENÉRICO DE CARGA ==========
  /**
   * Carga fotos aplicando paginación.
   * Pide ITEMS_PER_PAGE + 1 para detectar si hay página siguiente.
   */
  private loadPhotos(urlBase: string, searchLabel: string): void {
    this.lastUrlBase = urlBase;
    this.lastSearchLabel = searchLabel;
    this.currentSearch.set(searchLabel);

    const offset = this.currentPage * this.ITEMS_PER_PAGE;
    // Pedimos uno más para saber si hay siguiente página
    const limit  = this.ITEMS_PER_PAGE + 1;
    const separator = urlBase.includes('?') ? '&' : '?';
    const url = `${urlBase}${separator}offset=${offset}&limit=${limit}`;

    this.myPhotos = [];
    this.data.getPhotos(url).subscribe({
      next: (response) => {
        // Si vienen más de ITEMS_PER_PAGE, hay siguiente página
        const hasMore = response.length > this.ITEMS_PER_PAGE;
        // Mostramos solo los que corresponden a esta página
        this.myPhotos = response.slice(0, this.ITEMS_PER_PAGE);

        this.hasNextPage.set(hasMore);
        this.hasPrevPage.set(this.currentPage > 0);
        this.totalInPage.set(this.myPhotos.length);
        this.seePhotos = true;
        this.showUpload = false;
        this._change.markForCheck();
      },
      error: (err) => {
        console.error('Error cargando fotos:', err);
        this.myPhotos = [];
        this.hasNextPage.set(false);
        this.hasPrevPage.set(this.currentPage > 0);
        this.totalInPage.set(0);
        this._change.markForCheck();
      }
    });
  }

  // ========== NAVEGACIÓN DE PÁGINAS ==========
  public nextPage(): void {
    if (!this.hasNextPage()) return;
    this.currentPage++;
    this.loadPhotos(this.lastUrlBase, this.lastSearchLabel);
  }

  public previousPage(): void {
    if (this.currentPage <= 0) return;
    this.currentPage--;
    this.loadPhotos(this.lastUrlBase, this.lastSearchLabel);
  }

  /** Reinicia la paginación al cambiar de filtro/búsqueda */
  private resetAndLoad(urlBase: string, searchLabel: string): void {
    this.currentPage = 0;
    this.loadPhotos(urlBase, searchLabel);
  }

  // ========== ACCIONES DEL MENÚ ==========
  public onClickMyphotos(): void {
    this.resetAndLoad(
      `${this.urlMulti}${this.user_logged}`,
      'Mis Fotos'
    );
  }

  public onClickPhotosOf(index: number): void {
    this.resetAndLoad(
      `${this.urlMulti}${this.photoUsers[index].username}`,
      `Fotos de ${this.photoUsers[index].username}`
    );
  }

  public onClickAllPhotos(): void {
    this.resetAndLoad(this.urlAll, 'Todas las Fotos');
  }

  // ========== BÚSQUEDAS ==========
  public onSubmit(): void {
    const term = this.form.value.search?.trim() || '';
    if (!term) return;

    if (this.form.value.searchBy === 'title') {
      this.resetAndLoad(
        `${this.urlByTitle}${encodeURIComponent(term)}`,
        `por título "${term}"`
      );
    } else {
      this.resetAndLoad(
        `${this.urlByTag}${encodeURIComponent(term)}`,
        `por etiqueta "${term}"`
      );
    }
  }

  // ========== MODALES ==========
  public watchPhoto(id: number): void {
    this.seeModalViewer = true;
    this.photoId = id;
    this.viewerChild()?.open(id);
    this._change.markForCheck();
  }

  public editPhoto(id: number): void {
    this.seeModalEditor = true;
    this.photoId = id;
    document.body.style.overflow = 'hidden';
    this._change.markForCheck();
  }

  public deletePhoto(id: number): void {
    this.seeModalDelete = true;
    this.photoId = id;
    document.body.style.overflow = 'hidden';
    this._change.markForCheck();
  }

  public closeModalEditor(): void {
    this.seeModalEditor = false;
    document.body.style.overflow = 'auto';
    this._change.markForCheck();
  }

  public closeModalDelete(): void {
    this.seeModalDelete = false;
    document.body.style.overflow = 'auto';
    this._change.markForCheck();
  }

  // ========== OTROS ==========
  public uploadPhoto(): void {
    this.seePhotos = false;
    this.showUpload = true;
  }

  toggleDropdown(): void { this.isDropdownOpen = !this.isDropdownOpen; }
  closeDropdown(): void  { this.isDropdownOpen = false; }

  public ngOnInit(): void {
    this.data.getUsers(this.urlUsers).subscribe(response => {
      this.photoUsers = response;
      this._change.markForCheck();
    });
  }

  

}
